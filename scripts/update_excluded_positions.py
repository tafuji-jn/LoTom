#!/usr/bin/env python3
"""
MOUSEレイヤーのキーマップから excluded-positions を自動生成するスクリプト

使用方法:
    python scripts/update_excluded_positions.py

処理内容:
1. config/lotom.keymap から MOUSEレイヤーのbindingsを抽出
2. &trans と &to 0 以外のキー位置を特定
3. config/boards/shields/lotom/lotom_L.overlay と lotom_R.overlay の
   excluded-positions を更新
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List


def find_project_root():
    """プロジェクトルートを検索"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "config" / "lotom.keymap").exists():
            return current
        current = current.parent
    raise FileNotFoundError("プロジェクトルートが見つかりません")


def extract_mouse_layer_bindings(keymap_content: str) -> list[str]:
    """MOUSEレイヤーのbindingsを抽出"""
    # MOUSEレイヤーのbindingsブロックを検索（複数行対応）
    pattern = r'MOUSE\s*\{[^}]*?bindings\s*=\s*<([\s\S]*?)>;'
    match = re.search(pattern, keymap_content)
    if not match:
        raise ValueError("MOUSEレイヤーのbindingsが見つかりません")

    bindings_str = match.group(1)
    # 改行とコメントを削除し、キーを分割
    bindings_str = re.sub(r'/\*.*?\*/', '', bindings_str, flags=re.DOTALL)
    bindings_str = re.sub(r'//.*$', '', bindings_str, flags=re.MULTILINE)

    # &で始まるキーを抽出（引数も含む）
    # 例: &trans, &kp LC(C), &to 0, &mkp MB1
    keys = []
    current_key = ""
    in_key = False
    paren_depth = 0
    expecting_arg = False  # 引数を期待中（&to, &mo など）

    # 引数を取るbehavior
    arg_behaviors = {'&to', '&mo', '&lt', '&mt', '&kp', '&mkp', '&msc', '&sk'}

    for char in bindings_str:
        if char == '&':
            if current_key.strip():
                keys.append(current_key.strip())
            current_key = "&"
            in_key = True
            expecting_arg = False
        elif in_key:
            if char == '(':
                paren_depth += 1
                current_key += char
            elif char == ')':
                paren_depth -= 1
                current_key += char
            elif char in ' \t\n' and paren_depth == 0:
                # キーが完成したかチェック
                key_name = current_key.split()[0] if current_key else ""
                if key_name in arg_behaviors and len(current_key.split()) == 1:
                    # 引数を期待
                    expecting_arg = True
                    current_key += " "
                elif expecting_arg:
                    # 引数を取得完了
                    if current_key.strip():
                        keys.append(current_key.strip())
                    current_key = ""
                    in_key = False
                    expecting_arg = False
                else:
                    if current_key.strip():
                        keys.append(current_key.strip())
                    current_key = ""
                    in_key = False
            else:
                current_key += char

    if current_key.strip():
        keys.append(current_key.strip())

    return keys


def get_excluded_positions(keys: list[str]) -> list[int]:
    """&trans と &to 0 以外のキー位置を取得"""
    excluded = []
    for i, key in enumerate(keys):
        # &trans は除外
        if key == "&trans":
            continue
        # &to 0 は除外（スペースの有無に対応）
        if re.match(r'&to\s*0\b', key):
            continue
        excluded.append(i)
    return sorted(excluded)


def extract_default_layer_bindings(keymap_content: str) -> list[str]:
    """default_layerのbindingsを抽出"""
    pattern = r'default_layer\s*\{[^}]*?bindings\s*=\s*<([\s\S]*?)>;'
    match = re.search(pattern, keymap_content)
    if not match:
        return []

    bindings_str = match.group(1)
    bindings_str = re.sub(r'/\*.*?\*/', '', bindings_str, flags=re.DOTALL)
    bindings_str = re.sub(r'//.*$', '', bindings_str, flags=re.MULTILINE)

    keys = []
    current_key = ""
    in_key = False
    paren_depth = 0
    expecting_arg = False
    arg_behaviors = {'&to', '&mo', '&lt', '&mt', '&kp', '&mkp', '&msc', '&sk', '&mt_exit_AML_on_tap'}

    for char in bindings_str:
        if char == '&':
            if current_key.strip():
                keys.append(current_key.strip())
            current_key = "&"
            in_key = True
            expecting_arg = False
        elif in_key:
            if char == '(':
                paren_depth += 1
                current_key += char
            elif char == ')':
                paren_depth -= 1
                current_key += char
            elif char in ' \t\n' and paren_depth == 0:
                key_name = current_key.split()[0] if current_key else ""
                if key_name in arg_behaviors and len(current_key.split()) < 3:
                    expecting_arg = True
                    current_key += " "
                elif expecting_arg:
                    if current_key.strip():
                        keys.append(current_key.strip())
                    current_key = ""
                    in_key = False
                    expecting_arg = False
                else:
                    if current_key.strip():
                        keys.append(current_key.strip())
                    current_key = ""
                    in_key = False
            else:
                current_key += char

    if current_key.strip():
        keys.append(current_key.strip())

    return keys


def get_mt_exit_aml_positions(keys: list[str]) -> list[int]:
    """デフォルトレイヤーのmt_exit_AML_on_tapの位置を取得"""
    positions = []
    for i, key in enumerate(keys):
        if key.startswith("&mt_exit_AML_on_tap"):
            positions.append(i)
    return positions


def update_overlay_file(overlay_path: Path, excluded_positions: list[int]) -> bool:
    """overlayファイルのexcluded-positionsを更新"""
    content = overlay_path.read_text(encoding='utf-8')

    positions_str = " ".join(map(str, excluded_positions))
    new_line = f"    excluded-positions = <{positions_str}>;"

    # 既存のexcluded-positionsを更新
    pattern = r'(\s*)excluded-positions\s*=\s*<[^>]*>;'
    if re.search(pattern, content):
        new_content = re.sub(pattern, f'\\1excluded-positions = <{positions_str}>;', content)
    else:
        # zip_temp_layerブロックに追加
        pattern = r'(&zip_temp_layer\s*\{[^}]*)(})'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            new_content = content[:match.end(1)] + f"\n{new_line}\n" + content[match.start(2):]
        else:
            print(f"警告: {overlay_path}にzip_temp_layerブロックが見つかりません")
            return False

    if new_content != content:
        overlay_path.write_text(new_content, encoding='utf-8')
        return True
    return False


def main():
    try:
        root = find_project_root()
    except FileNotFoundError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    keymap_path = root / "config" / "lotom.keymap"
    # zip_temp_layer設定はlotom_L.overlayのみに存在
    overlay_paths = [
        root / "config" / "boards" / "shields" / "lotom" / "lotom_L.overlay",
    ]

    # keymapを読み込み
    keymap_content = keymap_path.read_text(encoding='utf-8')

    # MOUSEレイヤーのキーを抽出
    try:
        mouse_keys = extract_mouse_layer_bindings(keymap_content)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    print(f"MOUSEレイヤーのキー数: {len(mouse_keys)}")

    # excluded-positionsを計算（MOUSEレイヤーから）
    excluded = get_excluded_positions(mouse_keys)
    print(f"MOUSEレイヤーからの検出: {excluded}")

    # デフォルトレイヤーのmt_exit_AML_on_tap位置を追加
    default_keys = extract_default_layer_bindings(keymap_content)
    if default_keys:
        mt_exit_positions = get_mt_exit_aml_positions(default_keys)
        print(f"mt_exit_AML_on_tap位置: {mt_exit_positions}")
        excluded = sorted(set(excluded + mt_exit_positions))

    print(f"excluded-positions: {excluded}")

    # overlayファイルを更新
    for overlay_path in overlay_paths:
        if not overlay_path.exists():
            print(f"警告: {overlay_path}が存在しません")
            continue

        if update_overlay_file(overlay_path, excluded):
            print(f"更新: {overlay_path.name}")
        else:
            print(f"変更なし: {overlay_path.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
