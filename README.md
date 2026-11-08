# VOICEVOX Realtime Chat

Windows向けのデスクトップ音声会話アプリです。OpenAI Realtime APIでマイク音声を認識し、返答テキストをローカルのVOICEVOX Engineで読み上げます。

> 開発状況: v0.2.0 ではRealtime APIへのWebSocket接続、マイク音声の送信、サーバー側音声区間検出、返答テキストの受信、VOICEVOXによる読み上げを実装しています。割り込み時の再生キャンセル、発話の細かな分割再生、会話履歴の永続化は今後の改善対象です。

## 必要環境

- Windows 10/11
- Python 3.11 以降
- VOICEVOX Engine（ローカルで起動）
- OpenAI API key（Realtime API利用時に必要。ChatGPTのサブスクリプションとは別です）
- マイクとスピーカー

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

または run.bat を実行します。.venv があればそのPythonを使用します。

## 設定

config.yaml でモデル、VOICEVOX話者、読み上げ速度、マイク・スピーカーのデバイスを設定できます。

- audio.sample_rate: OpenAI Realtime PCM入力は 24000 Hz 固定です。変更しないでください。
- audio.input_device / output_device: sounddevice のデバイス番号またはデバイス名。null の場合はOS既定デバイス
- openai.instructions: Realtime APIに渡す応答指示
- voicevox.speaker_id: VOICEVOXの話者スタイルID

デバイス一覧は、Python環境で次を実行すると確認できます。

    python -c "import sounddevice as sd; print(sd.query_devices())"

## VOICEVOX

VOICEVOX Engineを起動し、既定の http://127.0.0.1:50021 でアクセスできるようにしてください。接続確認ボタンでEngineのバージョンを取得できます。会話開始前にEngineが利用可能であることを確認してください。

## 会話の使い方

1. OpenAI APIキーとVOICEVOX Engineを準備します。
2. アプリを起動し、「会話開始」を押します。
3. マイクに向かって話します。発話区間検出後、AIの返答テキストをVOICEVOXが読み上げます。
4. 終了するときは「会話停止」を押します。

Realtime APIの利用にはOpenAI APIの利用料金が発生します。利用状況と料金はOpenAIのAPIダッシュボードで確認してください。

## 開発・テスト

    pip install -e ".[dev]"
    ruff check .
    pytest

CIではPython 3.11でRuffとpytestを実行します。実機のマイク・スピーカーおよびVOICEVOX Engineを使う統合テストは別途必要です。

## 実装ロードマップ

1. 初期GUI、設定管理、VOICEVOX接続確認（v0.1.0）
2. Realtime API接続、マイク入力、テキスト応答、VOICEVOX読み上げ（v0.2.0）
3. 割り込み時の再生停止、音声再生とマイク入力のエコー対策
4. 応答テキストの分割読み上げ、デバイス選択UI、会話履歴
5. Windows向け配布パッケージとポータブル実行環境

## License

MIT
