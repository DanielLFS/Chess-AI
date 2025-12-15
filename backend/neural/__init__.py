"""
Neural network evaluation (NNUE - Efficiently Updatable Neural Network).

Modern engines like Stockfish use NNUE for +100 Elo improvement over
classical evaluation.

Planned architecture:
- Input: Board representation (768 features = 12 pieces × 64 squares)
- Hidden layers: Feature transformer + accumulator
- Output: Single evaluation score

Training approach:
- Self-play games for data generation
- Supervised learning from strong engine games
- Reinforcement learning (optional)

Libraries to consider:
- PyTorch (flexible, research-friendly)
- TensorFlow (production-ready)
- Custom C++ implementation (maximum speed)
"""
