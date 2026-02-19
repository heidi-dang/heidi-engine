# RLHF Integration Roadmap: Heidi Engine

This document outlines the strategy for integrating Reinforcement Learning from Human Feedback (RLHF) into the Heidi Engine to refine code generation quality.

## Objective
To align the model's code generation with human preferences for readability, correctness, and performance, using a combination of automated reward signals and human ranking.

## Phase 1: Preference Data Collection (Feedback Loop)
- **Goal**: Build a database of comparison pairs.
- **Component**: `scripts/06_collect_feedback.py`
- **Features**:
  - UI for comparing two model outputs for the same prompt.
  - Integration with `telemetry` to store "chosen" vs "rejected" samples.
  - Support for multi-language ranking.

## Phase 2: Reward Model (RM) Training
- **Goal**: Train a model to predict human scores.
- **Component**: `scripts/07_train_reward_model.py`
- **Architecture**:
  - Base: `microsoft/phi-2` or a smaller scalar-head classifier.
  - Loss: Pairwise ranking loss.
  - Feature: Use `heidi_cpp` to accelerate batch processing of code metrics as additional features for the RM.

## Phase 3: Alignment with PPO/DPO
- **Goal**: Fine-tune the generator model.
- **Component**: `scripts/08_rlhf_align.py`
- **Approach**:
  - **DPO (Direct Preference Optimization)**: Simpler, no separate RM needed at runtime. Preferred for initial rollout.
  - **PPO (Proximal Policy Optimization)**: More stable for complex tasks. Requires an actor, critic, and reward model.
  - Use Hugging Face `trl` library.

## Infrastructure Requirements
- **Hardware**: Minimum 24GB VRAM (3090/4090/A100) recommended for handling Actor + Critic models simultaneously.
- **Software**: `trl`, `peft`, `accelerate`, `bitsandbytes`.
- **Governance**: Integrated with `heidid` for resource-aware PPO training.

## Next Steps
1. Create prototype feedback UI using `streamlit` or the existing dashboard.
2. Define the exact format for the preference dataset.
