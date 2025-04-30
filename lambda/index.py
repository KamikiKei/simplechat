# lambda/index.py
import json
import os
import requests        # ← ここだけ外部呼び出し
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        # 1) リクエストボディを parse
        body = json.loads(event.get("body","{}"))
        message = body.get("message", "")
        conversation_history = body.get("conversationHistory", [])

        # 2) FastAPI／ngrok 経由用のペイロードをそのまま作成
        #    （必要なら messages の整形を追加）
        request_payload = {
            "message": message,
            "conversationHistory": conversation_history
        }

        # 3) MODEL_API_URL を環境変数から取得して /generate に POST
        api_url = os.environ["MODEL_API_URL"].rstrip("/") + "/generate"
        api_resp = requests.post(api_url, json=request_payload, timeout=15)
        api_resp.raise_for_status()
        response_body = api_resp.json()

        # 4) 返ってきた JSON の中身をチェック／取り出し
        if not response_body.get("success") or "response" not in response_body:
            raise Exception(f"APIエラー: {response_body}")

        assistant_response = response_body["response"]
        # 会話履歴に追記
        conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 5) 正常応答を返す
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type":"application/json",
                "Access-Control-Allow-Origin":"*",
                "Access-Control-Allow-Methods":"OPTIONS,POST",
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except Exception as e:
        # 何か例外が起きたら 500 を返却
        print("Error in lambda:", e)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type":"application/json",
                "Access-Control-Allow-Origin":"*",
                "Access-Control-Allow-Methods":"OPTIONS,POST",
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }