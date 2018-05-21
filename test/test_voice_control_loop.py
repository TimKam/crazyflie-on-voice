from src.voice_control_loop import generate_protocol_data, get_best_direction_match


def test_generate_protocol_data():
    assert generate_protocol_data('stop', None) == {'command': 'stop'}
    assert generate_protocol_data('start', None) == {'command': 'start'}
    assert generate_protocol_data('up', 100) == {'distance': [0, 0, 1]}
    assert generate_protocol_data('down', 200) == {'distance': [0, 0, -2]}
    assert generate_protocol_data('left', 50) == {'distance': [-0.5, 0, 0]}
    assert generate_protocol_data('right', 20) == {'distance': [0.2, 0, 0]}
    assert generate_protocol_data('forward', 10) == {'distance': [0, 0.1, 0]}
    assert generate_protocol_data('back', 40) == {'distance': [0, -0.4, 0]}


def test_get_best_direction_match():
    assert get_best_direction_match('nonsense') is None
    assert get_best_direction_match('app') == 'up'
    assert get_best_direction_match('town') == 'down'



