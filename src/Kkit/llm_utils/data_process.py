def input_output_to_messages(input_key, output_key, dataset, drop_input_output=True):
    def _fn(examples):
        return {
            "messages": [
                {"role": "user", "content": examples[input_key]},
                {"role": "assistant", "content": examples[output_key]}
            ]
        }
    
    return dataset.map(_fn, remove_columns=[input_key, output_key] if drop_input_output else None)
