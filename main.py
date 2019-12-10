# 標準ライブラリ
import time
# サードパーティライブラリ
import discord  # discord.py

# 自分のライブラリ


# BOT用チャンネルID
BOT_CHANNEL = 629111634467618850
TOKEN = "NjI5MTA3MzY3OTI5MTg0MzAx.XZU9CA.BMBYc0_J9j2m3UTbDJn-W9eZhR8"

client = discord.Client()

# %sが二つ必要。一つ目は名前、二つ目はチャンネル
check_in_msg = {"default": ["", "%sが%sに入室しました。"],
                "雑談": ["", "%sが%sしたがっている...", "%sが入室しました。\n%sのはじまりだ！", "%sが%sに参加した。"]}

check_out_msg = {"default": ["%sが%sから退出しました。"],
                 "雑談": ["%sが退出し%s部屋は解散しました。", "%sが退出し%sは終了しました。", "%sが%s部屋から退出しました。"]}


class AlreadyExists(Exception):
    pass


class AlreadyRemoved(Exception):
    pass


def get_msg(in_or_out: str, move_channel):
    if "in" == in_or_out:
        try:
            msg_list = check_in_msg[move_channel.name]
        except KeyError:
            msg_list = check_in_msg["default"]
    elif "out" == in_or_out:
        try:
            msg_list = check_out_msg[move_channel.name]
        except KeyError:
            msg_list = check_out_msg["default"]
    else:
        raise ValueError("\"in\"か\"out\"を第一引数にいれてください。")

    # 入ったチャンネルの人数（自分含む）
    member_num = len(move_channel.members)
    # msg_listの長さ
    list_len = len(msg_list)

    # メッセージ探し
    try:
        if list_len > member_num:
            msg = msg_list[member_num]
        else:
            msg = msg_list[list_len - 1]
    except IndexError:
        raise IndexError
    return msg


# グローバル変数使うのもなんだかなあと思ってクラスにしてみた。
# 2つの関数間で変数を共有したかった
class CheckTalkTime:
    def __init__(self):
        # 個人の通話開始時間を記録する辞書
        self.user_start_timestamp = {}
        # 雑談開始時間
        self.time_start_chatting = 0
        self.chatting = False

    def add_user(self, member: str):
        timestamp = time.time()
        if timestamp == self.user_start_timestamp.setdefault(member, timestamp):
            # 新しく追加できた時
            return
        else:
            # すでにキーが存在してた時
            raise AlreadyExists("同じユーザー(%s)がすでに通話中です。" % member)

    def remove_user(self, member: str):
        timestamp = time.time()
        if member not in self.user_start_timestamp:
            # memberのKeyが存在しなかった
            raise AlreadyRemoved("%sは存在しません。" % member)
        else:
            # memberのkeyが存在していた
            ans = timestamp - self.user_start_timestamp[member]
            self.user_start_timestamp.pop(member)
            return ans

    def start_chatting(self):
        if self.chatting:
            # すでに始まっている
            return -1
        else:
            self.time_start_chatting = time.time()
            self.chatting = True
            return 0

    def end_chatting(self):
        if self.chatting:
            ans = time.time() - self.time_start_chatting
            self.chatting = False
            return ans
        else:
            # 雑談が始まってない
            return -1


time_check = CheckTalkTime()

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')


# メンバーのボイスチャンネル出入り時に実行されるイベントハンドラ
@client.event
async def on_voice_state_update(member, before, after):
    # channelに変更があった時
    # メンバーが出入りした？
    # ミュートなどの状態変化も察知する
    if before.channel is not after.channel:
        member_name = str(member).split("#")
        try:
            # before が None は入ってきた時
            if before.channel is None:
                msg = get_msg("in", after.channel) % (member_name[0], after.channel.name)
                time_check.add_user(str(member))    # AlreadyExistsが起きるかも

            # afterがNone は出て行く時
            elif after.channel is None:
                msg = get_msg("out", before.channel) % (member_name[0], before.channel.name)
                msg += "(滞在時間: %s秒)" % time_check.remove_user(str(member))  # AlreadyRemovedが起きるかも

            # チャンネルを移動した時
            else:
                msg = get_msg("out", before.channel) % (member_name[0], before.channel.name)
                msg += "(滞在時間: %s秒)\n" % time_check.remove_user(str(member))
                msg += get_msg("in", after.channel) % (member_name[0], after.channel.name)
                time_check.add_user(str(member))
        except AlreadyRemoved as e:
            print(e)
        except AlreadyExists as e:
            print(e)
        except IndexError as e:
            print(e)

        print(msg)
        channel = client.get_channel(BOT_CHANNEL)
        await channel.send(msg)


if __name__ == "__main__":
    client.run(TOKEN)

