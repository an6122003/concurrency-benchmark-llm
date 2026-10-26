# Có cần chỉnh VRAM lên 96 GB? / Do you need the 96 GB setting?

## Tiếng Việt

RTX Spark có 128 GB RAM hợp nhất (unified memory), CPU và GPU dùng chung. Con số 50 GB trong NVIDIA App chỉ là phần dành riêng (chuyên dụng) cho GPU, không phải giới hạn cứng: khi model lớn hơn, Windows cho GPU dùng thêm bộ nhớ dùng chung từ chính 128 GB này, nên CUDA thấy tổng cộng khoảng 110 GB.

Mình test Nemotron 3.5 Super 120B (file 71,6 GB) ở mức 50 GB: cả 89/89 layer chạy trên GPU (49,3 GB chuyên dụng + 25,5 GB dùng chung), tốc độ 14,1 token/giây.

Nhưng bộ nhớ dùng chung chậm hơn. Cùng một model, khi nằm hoàn toàn ở vùng dùng chung, tốc độ sinh token giảm 12–15% (Qwen3.8-27B: 14,1 → 12,4 tok/s; Qwen3.6-35B-A3B: 62,6 → 53,0 tok/s), còn tốc độ đọc prompt gần như không đổi.

Thực tế khi đổi lên 96 GB rồi đo lại: Nemotron 3.5 Super chỉ nhanh hơn khoảng 2% khi sinh token (14,15 → 14,49 tok/s) và khoảng 10% khi đọc prompt (604 → 668 tok/s), vì ở mức 50 GB chỉ khoảng 1/3 model nằm ở vùng dùng chung. Riêng Qwen3.8-Flash-Next lại chậm hơn ở 96 GB (đọc prompt 838 → 269 tok/s), vì model này giữ bảng embedding 27 GB trong RAM hệ thống, mà ở 96 GB Windows chỉ còn 30,5 GB RAM.

Kết luận: không cần 96 GB mới chạy được model lớn. 96 GB chỉ nhỉnh hơn một chút với model có phần lớn nằm trên GPU, và có thể chậm hơn với model cần nhiều RAM hệ thống.

## English

The RTX Spark has 128 GB of unified memory shared by the CPU and GPU. The 50 GB in the NVIDIA App is the GPU's dedicated slice, not a hard limit: when a model is bigger, Windows lends the GPU shared memory from the same 128 GB, and CUDA sees about 110 GB in total.

Test: Nemotron 3.5 Super 120B (71.6 GB file) at the 50 GB setting ran with all 89 layers on the GPU (49.3 GB dedicated + 25.5 GB shared) at 14.1 tokens per second.

The catch: shared memory is slower. The same model running entirely from shared memory generates 12–15% fewer tokens per second (Qwen3.8-27B: 14.1 → 12.4 tok/s; Qwen3.6-35B-A3B: 62.6 → 53.0 tok/s), while prompt processing barely changes.

After switching to 96 GB and measuring again: Nemotron 3.5 Super is only about 2% faster at generating (14.15 → 14.49 tok/s) and about 10% faster at reading the prompt (604 → 668 tok/s), because at 50 GB only about a third of it sat in shared memory. Qwen3.8-Flash-Next got slower at 96 GB (prompt reading 838 → 269 tok/s): it keeps a 27 GB embedding table in system RAM, and at 96 GB Windows only has 30.5 GB of RAM left.

So you don't need 96 GB to run big models. It helps a little when most of a model sits on the GPU, and it can hurt a model that needs a lot of system RAM.

## How the shared-memory test worked

Same 50 GB setting, same llama-bench command (pp512, tg128, 3 repetitions). Run A loads the model normally, so its weights land in dedicated memory. Run B first starts an idle llama-server that fills the dedicated pool (46.7 GB), so the model's weights land in shared memory. Run A2 repeats A to rule out drift. Windows' per-process GPU memory counters confirm the placement of every run (`shared-memory-test/log.txt`).

## Evidence in this folder

- `vram-50gb-nemotron-3.5-super.txt`: the run log (setting, CUDA total, layers on GPU, memory in use, speed)
- `vram-50gb-nemotron-3.5-super-server.log`: llama.cpp's own log of the same run
- `demo-vram-50gb.ps1`: rerun the proof on camera with Task Manager > Performance > GPU open
- `vram-card.png` / `vram-card-vi.png`: 1080x1920 cards for the video
- `../shared-memory-test/`: the dedicated vs shared speed test
