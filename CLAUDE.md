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

## 定義済みマクロ
* `password1` 〜 `password9` の9つが定義済み
* Secretsが未設定のマクロは `bindings = <&none>` のまま（何も入力されない）
* 必要なものだけSecretsを設定すればOK

## フロー
1. LoTomへのpush/PR → GitHub Actionsがrepository_dispatchでLoTom_privateにトリガー送信
2. LoTom_privateがLoTomをチェックアウト
3. `scripts/convert_password.py`でSecretsのパスワードをZMKキーコードに変換
4. マクロ名で識別し、そのブロック内の`bindings = <&none>;`を変換後のキーコードで置換
5. ZMKファームウェアをビルド

## ファイル構成
* LoTom/.github/workflows/build.yml - LoTom_privateへトリガーを送信
* LoTom_private/.github/workflows/build.yml - 実際のビルドを実行
* LoTom_private/scripts/convert_password.py - パスワード→ZMKキーコード変換スクリプト

## keymapでのマクロ形式
```c
password1: password1 {
    compatible = "zmk,behavior-macro";
    #binding-cells = <0>;
    bindings = <&none>;
    label = "__PASSWORD1__";
};
```
* `bindings = <&none>;` がSecretsの値で置換される
* `label = "__PASSWORD1__";` も `label = "PASSWORD1";` に置換される
* DTSパーサー互換のため `/* */` 形式のコメントを使用

## パスワード追加時（10以上が必要な場合）
1. LoTom/config/lotom.keymapに新しいマクロ定義を追加
2. LoTom_private/.github/workflows/build.ymlのforループを拡張
3. LoTom_privateのSecretsに`PASSWORD10`などを追加



