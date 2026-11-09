# VOICEVOX Realtime Chat

Windows向けの音声会話アプリの基盤です。音声合成にはローカルのVOICEVOX Engineを使用します。

> **開発状況（v0.3.0）:** AI会話エンジンは未定です。特定のクラウドAPIに依存しない方針とし、会話エンジンの選定・接続処理は今後の検討項目としています。現時点で利用できるのは、デスクトップアプリの起動とVOICEVOX Engineの接続確認です。アプリからAIとの音声会話を行うことはできません。

## 必要環境

- Windows 10/11
- Python 3.11 以降
- VOICEVOX Engine（接続確認を行う場合）

マイクやスピーカーの音声入出力方式は、会話エンジンの選定後に決定します。

## セットアップ

PowerShellでリポジトリのルートを開きます。

    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e ".[dev]"
    Copy-Item config.example.yaml config.yaml

## 起動

    python run.py

または `run.bat` を実行します。`.venv` があればそのPythonを使用します。

## 設定

`config.yaml` では、VOICEVOX Engineの接続先と話者・読み上げ速度を設定できます。

- `voicevox.base_url`: VOICEVOX EngineのURL（既定値: `http://127.0.0.1:50021`）
- `voicevox.speaker_id`: VOICEVOXの話者スタイルID
- `voicevox.speed_scale`: 読み上げ速度

## VOICEVOX Engineの確認

1. VOICEVOXを起動します。
2. アプリを起動します。
3. 「VOICEVOX 接続確認」を押します。
4. バージョンが表示されれば接続できています。

既定の接続先は `http://127.0.0.1:50021` です。

## 会話機能について

AI会話エンジンは **未定** です。現時点では会話開始・停止、マイク音声の送信、AI応答の取得は行いません。利用するエンジンや接続方法が決まった段階で、改めて設計・実装します。

以前のバージョンで作成した `.env` にAPIキーが保存されていても、このバージョンでは読み込みません。不要であればローカルの `.env` を削除してください。APIキーの値を共有する必要はありません。

## 開発・テスト

    pip install -e ".[dev]"
    ruff check .
    pytest

CIではPython 3.11でRuffとpytestを実行します。VOICEVOX Engineとの実機接続確認は別途必要です。

## 実装状況

- [x] デスクトップGUIの起動
- [x] YAML設定の読み込み
- [x] VOICEVOX Engineの接続確認
- [ ] AI会話エンジンの選定（未定）
- [ ] 会話エンジンとの接続方式の設計・実装
- [ ] マイク・スピーカーの入出力方式の決定
- [ ] 会話履歴・割り込みなどの会話機能

## License

MIT
