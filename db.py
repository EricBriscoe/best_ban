import sqlalchemy
import pandas as pd
import riot
from tqdm import tqdm


def update_user(user, region):

    engine = get_engine()
    user_df = pd.read_sql(sql="SELECT * FROM public.lol_summoners", con=engine)
    if user.lower() not in [name.lower() for name in list(user_df["name"])]:
        summoner_dto = riot.get_summoner_info(user=user, region=region)
        summoner_df = pd.DataFrame(summoner_dto.json(), index=[0])
        summoner_df.to_sql(name="lol_summoners", con=engine, if_exists="append")
    return 1


def update_matches(user, region):
    engine = get_engine()
    all_match_df = pd.read_sql(sql="SELECT * FROM public.lol_matches", con=engine)
    matchlist_dto = riot.get_match_list(user=user, region=region)

    for match in tqdm(matchlist_dto.json()["matches"]):
        if match["gameId"] not in all_match_df["game_id"].values:
            match_dto = riot.get_match_by_id(match_id=match["gameId"], region=region)
            patch = match_dto.json()["gameVersion"].split(".")
            patch = "%s.%s" % (patch[0], patch[1])
            patch = float(patch)
            for participant in match_dto.json()["participants"]:
                match_df = pd.DataFrame(
                    data={
                        "game_id": match["gameId"],
                        "participant_id": participant["participantId"],
                        "account_id": match_dto.json()["participantIdentities"][
                            participant["participantId"] - 1
                        ]["player"]["accountId"],
                        "win": participant["stats"]["win"],
                        "champion_id": participant["championId"],
                        "patch": patch,
                    },
                    index=[0],
                )
                match_df.to_sql(name="lol_matches", con=engine, if_exists="append")


def get_losses(user, region):
    update_matches(user, region)
    engine = get_engine()
    losses = pd.read_sql(
        sql="SElECT game_id FROM public.lol_matches WHERE win=FALSE and account_id='%s'"
        % riot.get_acc_id(user, region),
        con=engine
    )
    return list(losses['game_id'].values)


def get_game_champs(game_id, winners_only):
    engine = get_engine()
    if winners_only:
        champs = pd.read_sql(
            sql="SELECT champion_id FROM public.lol_matches WHERE win=TRUE",
            con=engine
        )
    else:
        champs = pd.read_sql(
            sql="SELECT champion_id FROM public.lol_matches",
            con=engine
        )
    return list(champs['champion_id'].values)


def get_engine():
    engine = sqlalchemy.create_engine("postgresql://localhost:5432/postgres")
    engine.connect()
    return engine


if __name__ == "__main__":
    get_losses(user="jayhawker07", region="na1")
