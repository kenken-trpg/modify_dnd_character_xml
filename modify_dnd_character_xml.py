import xml.etree.ElementTree as ET
import argparse
import os
import re
import pathlib  # 追加

def modify_common_data(root):
    """
    共通データ (common data) を変更する。
    参照URL欄を追加する。
    """
    common_data = root.find(".//data[@name='common']")
    if common_data is not None:
        size_element = common_data.find("data[@name='size']")
        if size_element is not None:
            size_index = list(common_data).index(size_element)
            url_element = ET.Element("data", {"name": "参照URL"})
            common_data.insert(size_index + 1, url_element)
        else:
            print("エラー: <data name='size'/> が 'common' 内に見つかりません。")
            return False  # 処理を中止
    else:
        print("エラー: <data name='common'/> が見つかりません。")
        return False  # 処理を中止
    return True


def modify_action_data(root):
    """
    行動データ (action data) を変更する。
    HP, THP, イニシアチブ関連の修正。
    """
    action_data = root.find(".//data[@name='行動データ']")
    if action_data is None:
        print("エラー: <data name='行動データ'/> が見つかりません。")
        return False # 処理を中止

    # ヒット・ポイント -> HP
    hp_element = action_data.find("data[@name='ヒット・ポイント']")
    if hp_element is not None:
        hp_element.set("name", "HP")
    # 見つからない場合は警告を出し、処理は続行

    # THP追加
    if hp_element is not None:
        hp_index = list(action_data).index(hp_element)
        thp_element = ET.Element("data", {"name": "THP", "type": "numberResource", "currentValue": ""})
        action_data.insert(hp_index + 1, thp_element)

    # イニシアチブ -> イニシアチブ修正
    initiative_mod_element = action_data.find("data[@name='イニシアチブ']")
    if initiative_mod_element is not None:
        initiative_mod_element.set("name", "イニシアチブ修正")
        # 新しいイニシアチブ欄追加
        initiative_mod_index = list(action_data).index(initiative_mod_element)
        initiative_element = ET.Element("data", {"name": "イニシアチブ"})
        action_data.insert(initiative_mod_index + 1, initiative_element)
    # 見つからない場合は警告を出し、処理は続行
    return True

def modify_spell_data(root):
    """
    呪文データ (spell data) を変更する。
    呪文データを chat-palette に追加する。
    """
    chat_palette = root.find(".//chat-palette")
    if chat_palette is None:
        print("エラー: <chat-palette> が見つかりません。")
        return False #処理中止
    if chat_palette.text is None:
        chat_palette.text = ""

    spell_data = root.find(".//data[@name='呪文']")
    if spell_data is not None:
        for level_element in spell_data:
            level_name = level_element.get("name")

            if level_name == "初級呪文":
                target_string = r"▼初級呪文-----------------------------------"
            elif level_name.startswith("LV"):
                level_num = level_element.get("name")[2:]
                target_string = rf"▼{level_num}レベル呪文\(スロット数=(\d+)\)-----------------------------------"
            else:
                continue

            spell_texts = []
            for spell in level_element:
                if "name" in spell.attrib and spell.attrib["name"] != "スロット":
                    if spell.text:
                        spell_text = spell.text.strip().replace("\n", "　")
                        spell_texts.append(spell_text)

            combined_spell_text = "\n".join(spell_texts)

            match = re.search(target_string, chat_palette.text)
            if match:
                start, end = match.span()
                if level_name.startswith("LV"):
                    slot_number = match.group(1)
                    replacement_string = f"▼{level_num}レベル呪文(スロット数={slot_number})-----------------------------------"
                else:
                    replacement_string = target_string
                chat_palette.text = (
                    chat_palette.text[:start]
                    + replacement_string
                    + "\n"
                    + combined_spell_text
                    + chat_palette.text[end:]
                )
    return True


def modify_feature_data(root):
    """
    特徴データ (feature data) を変更する。
    特徴データを chat-palette に追加する。
    """
    chat_palette = root.find(".//chat-palette")  # chat_palette を再度検索
    if chat_palette is None: #modify_spell_dataで取得できなかった場合のため
        print("エラー: <chat-palette> が見つかりません。")
        return False  # 処理を中止
    if chat_palette.text is None:
        chat_palette.text = ""

    features_data = root.find(".//data[@name='特徴等']")
    if features_data is None:
        print("エラー: <data name='特徴等'> が見つかりません。")
        return False #処理中止

    target_string = "■特徴・特性======================================"
    feature_texts = []

    feature_names = ["背景", "人格的特徴", "尊ぶもの", "関わり深いもの", "弱味", "特徴・特性"]
    for feature_name in feature_names:
        feature_element = features_data.find(f"data[@name='{feature_name}']")
        if feature_element is not None and feature_element.text:
            feature_text = feature_element.text.strip().replace("\n", "　")
            feature_texts.append(f"【{feature_name}】{feature_text}")

    combined_feature_text = "\n".join(feature_texts)

    match = re.search(target_string, chat_palette.text)
    if match:
        start, end = match.span()
        chat_palette.text = (
            chat_palette.text[:end]
            + "\n"
            + combined_feature_text
            + chat_palette.text[end:]
        )
    return True


def modify_xml(input_file, output_file="modified.xml"):
    """
    XMLファイルを読み込み、各変更関数を呼び出し、結果を書き出す。
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            xml_string = f.read()
        root = ET.fromstring(xml_string)
    except FileNotFoundError:
        print(f"エラー: 入力ファイル '{input_file}' が見つかりません。")
        return
    except ET.ParseError as e:
        print(f"XML解析エラー: {e}")
        return

    # 各変更関数を呼び出す
    if not modify_common_data(root):
        return  # エラーがあった場合は処理を中止
    if not modify_action_data(root):
        return
    if not modify_spell_data(root):
        return
    if not modify_feature_data(root):
        return

    # XMLをファイルに書き出す
    ET.indent(root)
    try:
        modified_xml_string = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode('utf-8')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified_xml_string)
        print(f"XMLの変更に成功しました。出力は '{output_file}' に保存されました。")
    except Exception as e:
        print(f"出力ファイルへの書き込みエラー: {e}")



def main():
    parser = argparse.ArgumentParser(description="XMLキャラクターシートを変更するプログラム")
    parser.add_argument("input_file", help="入力XMLファイルのパス")
    parser.add_argument("-o", "--output", help="出力XMLファイルのパス (指定しない場合は modified_元ファイル名.xml)", required=False) #required=Falseに
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"エラー: 入力ファイル '{args.input_file}' が存在しません。")
        return

    # 出力ファイル名の決定
    if args.output:  # -o オプションが指定された場合
        output_file = args.output
    else:  # -o オプションが指定されなかった場合
        input_path = pathlib.Path(args.input_file)
        output_file = input_path.with_name(f"modified_{input_path.name}")


    modify_xml(args.input_file, output_file)

if __name__ == "__main__":
    main()
