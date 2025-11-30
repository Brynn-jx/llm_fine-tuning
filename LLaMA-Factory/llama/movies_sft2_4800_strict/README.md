---
library_name: peft
license: other
base_model: /home/wjx/.cache/modelscope/hub/models/LLM-Research/Meta-Llama-3-8B-Instruct
tags:
- base_model:adapter:/home/wjx/.cache/modelscope/hub/models/LLM-Research/Meta-Llama-3-8B-Instruct
- llama-factory
- lora
- transformers
pipeline_tag: text-generation
model-index:
- name: movies_sft2_4800_strict
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# movies_sft2_4800_strict

This model is a fine-tuned version of [/home/wjx/.cache/modelscope/hub/models/LLM-Research/Meta-Llama-3-8B-Instruct](https://huggingface.co//home/wjx/.cache/modelscope/hub/models/LLM-Research/Meta-Llama-3-8B-Instruct) on the movies_sft2 dataset.

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 5e-05
- train_batch_size: 1
- eval_batch_size: 8
- seed: 42
- gradient_accumulation_steps: 8
- total_train_batch_size: 8
- optimizer: Use adamw_torch with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: cosine
- lr_scheduler_warmup_steps: 100
- num_epochs: 3.0
- mixed_precision_training: Native AMP

### Training results



### Framework versions

- PEFT 0.17.1
- Transformers 4.57.1
- Pytorch 2.3.1+cu118
- Datasets 4.0.0
- Tokenizers 0.22.1