from background_task import background

from game_manager.models import Game
from game_manager.server_api import request_game_run


@background
def add_game_to_queue(game_id):
    game = Game.objects.get(pk=game_id)
    request_game_run(
        client1_name=game.get_request_sender_team().name,
        client1_language=game.get_request_sender_team().get_final_code().language,
        client1_path=game.get_request_sender_team().get_final_code().code_zip.path,
        client2_name=game.get_request_receiver_team().name,
        client2_language=game.get_request_receiver_team().get_final_code().language,
        client2_path=game.get_request_receiver_team().get_final_code().code_zip.path,
    )
