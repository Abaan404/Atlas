[![Contributors][contributors-shield]][contributors-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<br />
<p align="center">
  <a href="https://discord.com/api/oauth2/authorize?client_id=733548474699743262&permissions=8&scope=bot">
    <img src="https://cdn.discordapp.com/avatars/733548474699743262/090ef3221d920226e3f56ddfc947a8d8.webp" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center"><b>Atlas bot</b></h3>

  <p align="center">
    An open-source discord bot written in python!
    <br />
    <a href="https://github.com/Abaan404/Atlas/issues">Report Bugs</a>
    ·
    <a href="https://discord.com/oauth2/authorize?client_id=733548474699743262&permissions=1513962695871&scope=bot">Invite the Bot</a>
  </p>
</p>

# Atlas Bot

<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#contributing">Contributing</a></li>
  </ol>
</details>


Interested in knowing how the bot works? Wanna try to add some features? Feel free to do so! This project was made primarily as a way for me to get comfortable with python and as such may not receive constant updates. Feel free to add any features or fix bugs by <a href="#contributing">creating a pull request</a>. The bot is programmed using the amazing [discord.py](https://github.com/Rapptz/discord.py) library, you can read their docs [here](https://discordpy.readthedocs.io/en/stable/)!

Before starting, keep in mind the bot is ran under a containerized instance, so most windows commands or scrips won't function. Instead, you may work on the bot using [wsl](https://docs.microsoft.com/en-us/windows/wsl/install-win10#manual-installation-steps) if you choose to do so.

# Getting Started

## Prerequisites

* Docker
  ```sh
  sudo pacman -S docker # or through an equivalent package manager 
  ```
* A lavalink config file (`application.yml`). Below is an example config from the [lavalink repo](https://github.com/freyacodes/Lavalink)
  ```sh
  mkdir lavalink
  curl https://raw.githubusercontent.com/freyacodes/Lavalink/master/LavalinkServer/application.yml.example > lavalink/application.yml```
* A Discord Bot token
  ```
  Read the instructions at https://discordpy.readthedocs.io/en/latest/discord.html#creating-a-bot-account to get a bot token from discord
  ```
## Installation


1. Clone the repo
   ```sh
   git clone https://github.com/Abaan404/Atlas
   ```
2. Create a lavalink config (`./lavalink/application.yml`)
   ```sh
   https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example
   ```
3. create a `.env` file in the project root or supply the bot with the following environment variables
   ```sh
   BOT_TOKEN=
   LAVALINK_PASSWORD=
   SPOTIFY_CLIENT_ID=
   SPOTIFY_CLIENT_SECRET=
   ```
4. Then build and deploy the images
   ```sh
   docker compose up -d
   ```
# Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch `git checkout -b feature/AmazingFeature`
3. Commit your Changes `git commit -m 'Add some AmazingFeature'`
4. Push to the Branch `git push origin feature/AmazingFeature`
5. Open a Pull Request

## License

Distributed under the GNU GPLv3 License. See `LICENSE` for more information.

## Acknowledgements
* Used a README Template by [othneildrew/Best-README-Template](https://github.com/othneildrew/Best-README-Template)
* Used [freyacodes/Lavalink](https://github.com/freyacodes/Lavalink) and [lavaplayer-fork](https://github.com/Walkyst/lavaplayer-fork) for music integration using [cloudwithax/pomice](https://github.com/cloudwithax/pomice)
* Used [Rapptz/discord.py](https://github.com/Rapptz/discord.py) as the primary library for the bot

[contributors-shield]: https://img.shields.io/github/contributors/Abaan404/Atlas.svg?style=for-the-badge
[contributors-url]: https://github.com/Abaan404/Atlas/graphs/contributors
[issues-shield]: https://img.shields.io/github/issues/Abaan404/Atlas.svg?style=for-the-badge
[issues-url]: https://github.com/Abaan404/Atlas/issues
[license-shield]: https://img.shields.io/github/license/Abaan404/Atlas.svg?style=for-the-badge
[license-url]: https://github.com/Abaan404/Atlas/blob/master/LICENSE.txt