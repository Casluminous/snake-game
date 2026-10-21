# Rắn săn mồi — Bài 4

Game rắn săn mồi viết bằng Python + pygame.

## Cách chơi

| Phím | Chức năng |
|---|---|
| Mũi tên / WASD | Di chuyển |
| P | Tạm dừng |
| R | Chơi lại (khi thua) |
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
