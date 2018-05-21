from src.voice_control_loop import generate_protocol_data, get_best_direction_match


def test_generate_protocol_data():
    assert generate_protocol_data('stop', None) == {'command': 'stop'}


def test_get_best_direction_match():
    assert get_best_direction_match('nonsense') is None



