\# プロジェクト概要



* このプロジェクトはキーボードのファームウェアにおけるconfigリポジトリである
* オートマウスレイヤーのカスタマイズは次のURLが参考になる  

1. https://zenn.dev/kot149/articles/zmk-auto-mouse-layer
2. https://zenn.dev/kot149/articles/zmk-input-processor-cheat-sheet



\#  注意点

* リモートリポジトリはpublicなので個人情報などはpushしないこと
* プロパティやオプションを推測で追加することは禁止。必ず公式ドキュメントや参考URLを確認してから使用すること

\# パスワードマクロの仕組み

## 概要
パスワードなどの機密情報をファームウェアに埋め込むため、LoTom_privateリポジトリと連携してビルドを行う。

## フロー
1. LoTomへのpush/PR → GitHub Actionsがrepository_dispatchでLoTom_privateにトリガー送信
2. LoTom_privateがLoTomをチェックアウト
3. `scripts/convert_password.py`でSecretsのパスワードをZMKキーコードに変換
4. `lotom.keymap`内の`<&none>;  // __PASSWORD1__`を変換後のキーコードで置換
5. ZMKファームウェアをビルド

## ファイル構成
* LoTom/.github/workflows/build.yml - LoTom_privateへトリガーを送信
* LoTom_private/.github/workflows/build.yml - 実際のビルドを実行
* LoTom_private/scripts/convert_password.py - パスワード→ZMKキーコード変換スクリプト

## keymapでのプレースホルダー形式
```c
bindings = <&none>;  // __PASSWORD1__
```
この形式により、keymap editorでもパース可能かつビルド時に置換可能。

## パスワード追加時
1. LoTom_privateのSecretsに`PASSWORD3`などを追加
2. LoTom_private/.github/workflows/build.ymlの置換処理に追加
3. LoTom/config/lotom.keymapにマクロ定義を追加



