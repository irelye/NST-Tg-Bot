![img](https://cdn4.telesco.pe/file/ALWGlLDtIyJ1cwkfaCZCNyt2m3B0ngxgBgKugowxBgn2O9JdKJudsWV9ZisELCcxqsq7vKWZ-HwFz3VD9slH5YH61WlRJNEkUMsGzMCDMEGeEuH5OQ8m25xyeIZSAHxW8SRNDXAkt-pek8tTP8fPZltatY1K1G6smm-4zeUJl0aemzpZyOeXpwoLtTfI3OnSBCQzwXxYxL222n5Rp6UNKIFEbrJi5OTqnUy6SOewL4wJAk5JPPlrLFxTVAFR2LNmGI6n_VTZI_P12ukcVrXZ2q5y7oqwwmjfMhwoBTtRcAIotJUhDWtThl045Ji6AOp3jUaoa09VsoAB1CPWdTKYgw.jpg)

# NST-Tg-Bot
A Telegram bot that performs fast patch-based style transfer [algorithm](https://arxiv.org/pdf/1612.04337.pdf) by Chen and Schmidt.
You can find it [here](https://t.me/fiflyc_nst_bot) but it's not working cause it's not hosted. Free servers have too low memory limitation for this algorithm.

## Running
If you want to run it (for a some reason) you can simply type
`python3 run.py -t=[TOKEN]`
where `[TOKEN]` are your valid token received from [BotFather](https://t.me/BotFather).
Other optional arguments are:
* `-d` -- path where bot will store Telegram's files. Default: `./saved`
* `-b` -- path where bot will store MySQL databases. Default: `./db`
* `-c` -- clearing cache dir time in seconds. It means that bot periodically deletes files it received. Default: `7200` (2 hours).
* `-w` -- waiting time for user's second image. If image wasn't received before that time, bot may forget user's previous query. Default: `1200` (20 minutes).

## Usage
Write `/content` in an image description to change it's style. You can also type `/content` in a reply to a message with the image.

Do the same thing with `/style` passing an artwotk which style you want to use.

After you send all the inputs, bot will transfer style. Average waiting time: 40 seconds.
