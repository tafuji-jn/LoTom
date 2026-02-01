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

# 外部モジュール

## zmk-tri-state
* リポジトリ: https://github.com/dhruvinsh/zmk-tri-state
* 用途: ウィンドウ/タブ切り替え用swapper

### 概要
ZMK本体にはない「tri-state」behaviorを提供する外部モジュール。
レイヤー内でモディファイアを押し続け、レイヤーを離れると自動的に解除する動作を実現。

### west.ymlへの追加
```yaml
remotes:
  - name: dhruvinsh
    url-base: https://github.com/dhruvinsh
projects:
  - name: zmk-tri-state
    remote: dhruvinsh
    revision: main
```

### 定義済みswapper

| behavior | 動作 | bindings |
|----------|------|----------|
| `&swapper` | Alt+Tab（ウィンドウ切替） | `<&kt LALT>, <&kp TAB>, <&kt LALT>` |
| `&tab_next` | Ctrl+PageDown（次のタブ） | `<&kt LCTRL>, <&kp PAGE_DOWN>, <&kt LCTRL>` |
| `&tab_prev` | Ctrl+PageUp（前のタブ） | `<&kt LCTRL>, <&kp PAGE_UP>, <&kt LCTRL>` |

全てShift併用可能（ignored-key-positionsに位置8, 26を含む）

### パラメータ
* `bindings`: 3つのbinding
  * 1番目: 開始時のアクション（モディファイア押下）
  * 2番目: 繰り返しアクション（Tabなど）
  * 3番目: 終了時のアクション（モディファイア解除）
* `ignored-key-positions`: 終了トリガーを発火させないキー位置
  * swapper自身の位置を含める
  * Shift併用のため位置8（sk LSHIFT）と26（mt LSHIFT）を含める

### 動作
1. 最初に押す → モディファイア押し + キー
2. 続けて押す → キー（モディファイアは押したまま）
3. Shiftを押しながら → 逆方向に切り替え
4. ignored-key-positions以外のキーを押す or レイヤーを離れる → モディファイアを解除

### 新しいswapper追加時
1. keymapのbehaviorsセクションに新しいtri-state定義を追加
2. ignored-key-positionsに必要なキー位置を設定
3. Keymap Editorから`&新しいswapper名`で選択可能

# オートマウスレイヤー (zip_temp_layer)

## 概要
トラックボールを操作すると自動的にMOUSEレイヤー(レイヤー1)に切り替わる機能。

## 設定ファイル
* `config/boards/shields/lotom/lotom_L.overlay`
* `config/boards/shields/lotom/lotom_R.overlay`

## パラメータ

### trackball_listener
```c
input-processors = <&pointer_accel &zip_temp_layer 1 100000>;
```
* `&pointer_accel`: 加速度処理
* `&zip_temp_layer 1 100000`: レイヤー1に切り替え、タイムアウト100秒（実質無効）

### zip_temp_layer設定
```c
&zip_temp_layer {
    require-prior-idle-ms = <350>;
    excluded-positions = <0 10 11 12 22 23 24 25 26 34 35 36>;
};
```

## excluded-positions

マウスレイヤー解除をトリガーしないキー位置のリスト。これらのキーを押してもマウスレイヤーに留まる。

### 現在の設定値

| 位置 | キー | 説明 |
|------|------|------|
| 0 | mt_exit_AML_on_tap LSHFT ESC | 左上Shift（ホールド時はレイヤー維持、タップ時は解除） |
| 10 | mkp MB1 | マウスボタン1（左クリック） |
| 11 | msc SCRL_UP | スクロールアップ |
| 12 | mkp MB2 | マウスボタン2（右クリック） |
| 22 | mkp MB1 | マウスボタン1（左クリック） |
| 23 | mkp MB3 | マウスボタン3（中クリック） |
| 24 | mkp MB2 | マウスボタン2（右クリック） |
| 25 | mo 2 | SCROLLレイヤーへの一時切替 |
| 26 | mt_exit_AML_on_tap LEFT_SHIFT Z | 左下Shift（ホールド時はレイヤー維持、タップ時は解除） |
| 34 | mkp MB1 | マウスボタン1（左クリック） |
| 35 | msc SCRL_DOWN | スクロールダウン |
| 36 | mkp MB2 | マウスボタン2（右クリック） |

### キー位置の計算方法
keymapのキー配置（0から順番）:
```
位置0      位置1        ← エンコーダー行
位置2-7    位置8-13     ← 上段
位置14-19  位置20-25    ← 中段
位置26-31  位置32-37    ← 下段
位置38-43  位置44-47    ← 親指行
```

### マウスキー追加時
MOUSEレイヤーにキーを追加すると、ビルド時に`scripts/update_excluded_positions.py`が自動的に`excluded-positions`を更新します。

**自動検出対象:**
- MOUSEレイヤー: `&trans`と`&to 0`以外のすべてのキー
- デフォルトレイヤー: `&mt_exit_AML_on_tap`の位置（Shift+クリック対応）

**手動での追加は不要です。**

### スクリプトの動作
1. `config/lotom.keymap`のMOUSEレイヤーをパース
2. `&trans`と`&to 0`以外のキー位置を抽出
3. デフォルトレイヤーの`&mt_exit_AML_on_tap`位置を追加
4. `config/boards/shields/lotom/lotom_L.overlay`の`excluded-positions`を更新
5. GitHub Actionsで自動実行（変更があればコミット）

### ローカルでの実行
```bash
python scripts/update_excluded_positions.py
```



