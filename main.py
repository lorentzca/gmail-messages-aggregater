from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import defaultdict
from retry import retry
import sys
import os
import re

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]
TOKEN_FILE_NAME = "token.json"
EMAIL_ADDRESS = sys.argv[0]


def creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        with open("token.json", 'w') as token:
            token.write(creds.to_json())
    return creds


def extract_email_addresses(text):
    match = re.search(r'<(.+?)>', text)
    if match:
        email = match.group(1)
        return email
    else:
        # マッチしない場合「"サンプル（EXAMPLE）" <info@example.com>」のような形式ではなく
        # info@example.com のようにアドレスのみの場合と判断。雑だけど。
        return text


def sort_email_counts(email_counts, top):
    print(f"\nTOP {top} は以下です。")
    sorded_email_counts_items = sorted(
        email_counts.items(), key=lambda x: x[1], reverse=True)
    for email, count in sorded_email_counts_items[:top]:
        print(f"{email}: {count}")


@retry(tries=3, delay=2)
def get_email_list(request):
    results = request.execute()
    return results


@retry(tries=3, delay=2)
def get_email_detail(service, message_id):
    txt = service.users().messages().get(
        userId='me', id=message_id).execute()
    return txt


def main():
    try:
        c = creds()
        service = build('gmail', 'v1', credentials=c)
        max_results = 500  # 最大 500
        email_counts = defaultdict(int)
        consumed_token = 0

        request = service.users().messages().list(
            userId='me', maxResults=max_results)

        while request is not None:
            results = get_email_list(request)
            consumed_token += max_results
            print(f"\n現時点で {consumed_token} 個のリストを取得しました。")
            messages = results.get('messages')

            for msg in messages:
                txt = get_email_detail(service, msg['id'])
                payload = txt['payload']
                headers = payload['headers']
                for d in headers:
                    if d['name'] == 'From':
                        sender = d['value']
                        sender_email_address = extract_email_addresses(sender)
                        email_counts[sender_email_address] += 1
                print("From: ", sender_email_address)

            # # 検証用に適当なところで切り上げるためのコード
            # if consumed_token > 19:
            #     break

            print("\n現時点の集計結果です。")
            sort_email_counts(email_counts, 10)

            request = service.users().messages().list_next(request, results)

        # 最終的にはトップ 50 を出す。
        sort_email_counts(email_counts, 50)

        return "end"
    except HttpError as error:
        print(f'An error occurred: {error}')


if __name__ == "__main__":
    main()
