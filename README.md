# VOICEVOX Realtime Chat

Windows向けのデスクトップ音声会話アプリです。OpenAI Realtime APIで会話を行い、AIの返答音声をローカルのVOICEVOX Engineで読み上げることを目指します。

> 開発状況: v0.1.0 は初期セットアップ版です。GUI、設定読み込み、VOICEVOX Engineへの接続確認と音声合成HTTPクライアントを用意しています。マイク入力・Realtime APIの双方向音声会話・割り込み再生は今後の実装対象です。

## 必要環境

- Windows 10/11
- Python 3.11 以降
- VOICEVOX Engine（ローカルで起動）
- OpenAI API key（Realtime API利用時に必要。ChatGPTのサブスクリプションとは別です）

## セットアップ

PowerShellでリポジトリのルートを開きます。

    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e ".[dev]"
    Copy-Item config.example.yaml config.yaml
    Copy-Item .env.example .env

.env の OPENAI_API_KEY にAPIキーを設定してください。APIキーはGitにコミットしないでください。

## 起動

    python run.py

または仮想環境を有効化した状態で run.bat を実行します。

## VOICEVOX

VOICEVOX Engineを起動し、既定の http://127.0.0.1:50021 でアクセスできるようにしてください。接続確認ボタンでEngineのバージョンを取得できます。

## 開発

    pip install -e ".[dev]"
    ruff check .
    pytest

## 実装ロードマップ

1. 初期GUI、設定管理、VOICEVOX接続確認（v0.1.0）
2. Realtime API WebSocket接続と会話イベント処理
3. マイク入力、音声ストリーム、発話区間検出
4. 返答テキストの分割とVOICEVOX逐次合成・再生
5. 発話中の割り込み、再生キャンセル、会話履歴
6. Windows向け配布パッケージとポータブル実行環境

## License

MIT
