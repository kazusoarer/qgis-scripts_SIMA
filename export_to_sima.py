import os
from qgis.core import QgsProject, QgsWkbTypes

# ------------- カスタマイズ部分 ------------- #

# 1. レイヤー名を指定（QGISのレイヤーパネルで確認できる名前）
layer_name = 'tochi_poly'  # 実際のレイヤー名に変更してください

# ------------- カスタマイズ部分終了 ------------ #

# レイヤーを取得
layers = QgsProject.instance().mapLayersByName(layer_name)
if not layers:
    print(f"レイヤー '{layer_name}' が見つかりません。名前を確認してください。")
else:
    layer = layers[0]

    # 選択されたフィーチャーを取得
    selected_features = layer.selectedFeatures()
    print(f"選択されたフィーチャー数: {len(selected_features)}")
    if not selected_features:
        print("選択されたポリゴンがありません。処理を終了します。")
    else:
        # デスクトップのパスを取得
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        output_filename = 'SIMA_output.sim'
        output_path = os.path.join(desktop_path, output_filename)

        # データを格納するリスト
        # List of tuples: (vertex_id, chiban_id, x, y, z)
        vertices = []

        # List of dictionaries: {'district_id': id, 'chiban_name': name, 'vertex_ids': [ids]}
        districts = []

        vertex_id = 1
        district_id = 1

        for feature in selected_features:
            geom = feature.geometry()
            print(f"Processing feature ID {feature.id()}")

            # ジオメトリタイプのチェック
            if QgsWkbTypes.geometryType(geom.wkbType()) != QgsWkbTypes.PolygonGeometry:
                print(f"フィーチャーID {feature.id()} はポリゴンジオメトリではありません。スキップします。")
                continue  # ポリゴンでないフィーチャーはスキップ

            if geom.isMultipart():
                polygons = geom.asMultiPolygon()
            else:
                polygons = [geom.asPolygon()]

            # 地番名称を自動付与
            chiban_name = f'chiban_{district_id}'

            current_district_vertex_ids = []

            for polygon in polygons:
                for ring in polygon:
                    for point in ring:
                        x = point.x()
                        y = point.y()
                        z = 0  # デフォルトでZ座標を0に設定
                        # 追加
                        vertices.append( (vertex_id, district_id, x, y, z) )
                        current_district_vertex_ids.append(vertex_id)
                        vertex_id +=1

            # 区画データを追加
            districts.append({
                'district_id': district_id,
                'chiban_name': chiban_name,
                'vertex_ids': current_district_vertex_ids
            })

            district_id +=1

        # 書き込み
        try:
            with open(output_path, 'w', encoding='shift_jis') as file:  # 文字コードをShift_JISに変更
                # ヘッダー部分の記述
                file.write("G00,01,INFINITY現場ﾃﾞｰﾀ ,\n")
                file.write("Z00,座標ﾃﾞｰﾀ,\n")
                file.write("A00,\n")

                # A01 lines
                for v in vertices:
                    vid, cid, x, y, z = v
                    line = f"A01,{vid},{cid},{x},{y},{z},,\n"
                    file.write(line)

                # A99: 座標データセクションの終了
                file.write("A99,\n")

                # 区画データセクションの開始
                file.write("Z00,区画ﾃﾞｰﾀ,\n")

                # D00 and B01 lines
                for district in districts:
                    did = district['district_id']
                    cname = district['chiban_name']
                    file.write(f"D00,{did},{cname},{did},\n")
                    for vid in district['vertex_ids']:
                        file.write(f"B01,{vid},{did},,\n")

                # 区画データセクションの終了
                file.write("D99,\n")

            print(f"SIMA形式のデータがデスクトップに保存されました。ファイル名: '{output_filename}'")

        except Exception as e:
            print(f"ファイルの書き込み中にエラーが発生しました: {e}")
