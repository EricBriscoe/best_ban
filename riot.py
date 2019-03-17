import configparser
import requests
import db
import pandas as pd
import time

config = configparser.ConfigParser()
config.read("config.ini")


def get_match_list(user, region):
    api_key = (config.get("DEFAULT", "api_key"),)
    acc_id = get_acc_id(user=user, region=region)
    matchlist_dto = requests.get(
        "https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/%s" % acc_id,
        params={"api_key": api_key},
    )
    return matchlist_dto


def get_acc_id(user, region):
    engine = db.get_engine()
    acc_df = pd.read_sql(sql="SELECT t.*, CTID FROM public.lol_summoners t", con=engine)
    if user.lower() not in [name.lower() for name in list(acc_df["name"])]:
        db.update_user(user=user, region=region)

    acc_df = pd.read_sql(
        sql="SELECT t.*, CTID FROM public.lol_summoners t WHERE name='%s'" % user,
        con=engine,
    )
    return acc_df["accountId"][0]


def get_summoner_info(user, region):
    api_key = (config.get("DEFAULT", "api_key"),)
    summoner_dto = requests.get(
        "https://%s.api.riotgames.com/lol/summoner/v4/summoners/by-name/%s"
        % (region, user),
        params={"api_key": api_key},
    )
    return summoner_dto


def get_match_by_id(match_id, region):
    api_key = (config.get("DEFAULT", "api_key"),)
    match_dto = requests.get(
        "https://%s.api.riotgames.com/lol/match/v4/matches/%s" % (region, match_id),
        params={"api_key": api_key},
    )
    while match_dto.status_code == 429:
        time.sleep(120)
        match_dto = requests.get(
            "https://%s.api.riotgames.com/lol/match/v4/matches/%s" % (region, match_id),
            params={"api_key": api_key},
        )
    return match_dto


def get_best_bans(user, region):
    loss_ids = db.get_losses(user,region)
    champ_loss_counter = {}
    for loss_id in loss_ids:
        champ_ids = db.get_game_champs(game_id=loss_id, winners_only=True)
        for cid in champ_ids:
            try:
                champ_loss_counter[cid] += 1
            except KeyError:
                champ_loss_counter[cid] = 1

    loss_df = pd.DataFrame(data={'champion_id':[], 'loss_count':[]})
    for cid, loss_count in champ_loss_counter.items():
        df = pd.DataFrame(data={'champion_id':[cid], 'loss_count': [loss_count]})
        loss_df.append(df)
    loss_df.sort_values(by='loss_count')
    print(loss_df)


if __name__ == "__main__":
    get_best_bans(user="NoLoseJustLearn", region="na1")
