def test_callback_measurement_retains_baseline_advice_and_duplicate_samples(tmp_path):
    from eval.advice_callbacks import measure
    from test_milestone_entrypoints import process_project
    root = tmp_path / 'project'; root.mkdir(); process_project(root)
    value = measure(root, changed='cli.py', hosts=['claude'], repeats=1, seconds=2)
    sample = value['samples'][0]
    assert sample['baseline']['exit_code'] == sample['advised']['exit_code'] == 0
    assert sample['advised']['has_advice']
    assert not sample['duplicate']['has_advice']
    assert sample['duplicate']['ms'] >= 0
