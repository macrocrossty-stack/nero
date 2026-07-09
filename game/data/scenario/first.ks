; ============================================
; first.ks — エントリーポイント（簡易タイトル）
; 『眠り姫と黒豹の物語』（仮）
; 本格的なタイトル画面（ボタンUI）は後日 title.ks として実装予定。
; ============================================

[title name="眠り姫と黒豹の物語（仮）"]

*start

[cm]
[bg storage="bg_forest_night.jpg" time=100]
[wait time=500]

#
眠り姫と黒豹の物語[r]
[r]
—— クリックで、絵本をひらく ——[p][cm]

[jump storage="prologue.ks" target="*start"]
