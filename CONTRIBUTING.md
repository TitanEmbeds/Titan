# Contributing to Titan Embeds
There are many ways to contribute to Titan. There is no one right method to contribute. As long as your Pull Request is valid and is beneficial to the project, we'll take it. Whether you are a designated developer of this project, or just a seasonal hacker who want to fix a mistake that we probably made, you're welcomed to help as long as you abide by these guidelines. This document outlines of the practices and mistakes involving with contributing to the project.

## Development Environment
For those who would like to run the codebase yourself, you may follow the instructions to the webapp and discordbot to setup the components on your own server. You could however also develop the code on Cloud9. It is free* and very simple to get it off running under ten minutes or less. Either way, if you would like to contribute to the project, I strongly advise you to run Titan on a development server. Making changes on a dev server has many benefits. Especially if you are making changes other than wording issues, the GitHub editor is not the way to go. You may follow these steps to run Titan with Cloud9.

*If you happen to have a credit/debit card, you may skip steps 1-3 (With steps 4-5 links modified) to use the official Cloud9 site. They just use the card as a verification form and will refund your money immediately.*
**Credit to <https://forum.freecodecamp.com/t/can-i-create-a-cloud9-without-credit-card/25334/13> to make this possible**
1. Sign up for this class, its free, and you need it for credentials to cloud9 <https://www.edx.org/course/introduction-computer-science-harvardx-cs50x>
2. Once you signed up, go to your email and confirm their verification link
3. Visit their version of cloud9 (same thing as the offical, just more cats) <http://cs50.io/> This is where you can use c9
4. Add your SSH key from this link <https://cs50.io/account/ssh> to github <https://github.com/settings/keys>
5. At the top right corner, click on New Workspace (To create one for Titan) <http://i.imgur.com/em8N1TX.png>
6. Fill in the details, click on Python as the template environment
7. Set the `Clone from Git or Mercurial url` to `git@github.com:EndenDragon/Titan.git` This should pull titan to your workspace.
8. Right click `cloud9_install.sh` file at the left sidebar and click run. This will set everything up.
9. Afterwards, just edit the respective config.py files in the webapp/discordbot directories and you are ready to go!
10. Now you're ready to run Titan... webapp! To make the webapp to work, rightclick `run_c9.py` file and click run. Congratz! It will tell you the exact url where your stuff is running at.
11. For discord bot, you can change the directory to the discordbot `cd discordbot/` and run `python3.5 run.py` to start the bot from the bash console!
12. To make the login system work, go back to your discord bot applications page... for the redirect uris, add these: `http://xxx.cs50.io/user/callback` and `http://xxx.cs50.io/user/dashboard`. Replacing the `xxx` with your subdomain url in the webapp. That outta make the login work! (Take note that there is no http**s** in http).
Now that you set everything up, take a step back and learn some ubuntu/bash to get familiar with it. Some things like git commit/push/pull, etc might be helpful. Maybe you can get phpmyadmin and inspect the database yourself, in gui form <https://community.c9.io/t/setting-up-phpmyadmin/1723>.

## Pull Requesting
If you do not have write access to the codebase, please make a fork of the project. Edit your changes on your fork and push it out onto GitHub. Afterwards, you may submit a pull request for your changes to be merged to the master branch (production). If you do however have write access to the repository, please create a branch and propose pull requests for me to merge into the production.

I have recently decided to restrict pushing into the master branch so that all commits to the codebase is complete and meaningful. The production environment is not used for testing and every new errors in the error log makes me feel a little bit sadder. Using branches and pull requests also means that I may squash and edit the commit messages before pulling into the master so they may look more nicer.
To create a new branch, run this command `git checkout -b <new branch name>`. Then use `git checkout <branch name>` to switch between branches.

Make sure that you thoughly test your changes so that it works and doesn't introduce new bugs. *I won't merge any pull requests until your changes are complete.* I do not like to accept features that are "half done" as these may be left abandoned at any time and may look odd. Please keep in mind to create one branch/pull request for every new feature. 

Although I try to be as lenient as possible, please follow the best coding and git practices. If you need help, please join the Discord server and talk to me - EndenDragon. I don't bite. I am more than welcomed to help you if you're stuck during the process of contribution. Sorry if the guidelines above are a bit scary, I just wanted to establish some common ground. Happy hacking, and thank you for making Titan better for everyone!
