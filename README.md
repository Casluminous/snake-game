# Rắn săn mồi — Bài 4

Game rắn săn mồi viết bằng Python + pygame.

## Cách chơi

| Phím | Chức năng |
|---|---|
| W A S D | Di chuyển |
| P | Tạm dừng |
| R | Chơi lại (mọi lúc) |
| Nút CHƠI LẠI | Bấm chuột để chơi lại khi thua |
| Esc | Thoát |

## Quy tắc

- Mồi đỏ: +1 điểm, rắn dài thêm 1 đốt
- Mồi vàng: chỉ tồn tại 5 giây, ăn được +5 điểm
- Cứ ăn đủ 5 mồi, rắn tăng tốc (tối đa 16 bước/giây)
- Đâm vào tường hoặc thân mình: thua

## Chạy game

```bash
pip install pygame        # pygame-ce nếu Python >= 3.14
python snake.py
```

## Tự kiểm tra logic

```bash
python snake.py --selftest
```

## Tài liệu

- `docs/Bai-4-Ran-san-moi-Bao-cao-cach-lam.docx` — báo cáo cách làm và các thành phần chính
- `docs/Bai-4-Ran-san-moi-Ly-thuyet-va-ky-thuat.pptx` — slide lý thuyết thuật toán và kỹ thuật
