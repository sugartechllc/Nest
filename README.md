# Nest
Nest Thermostat Data to CHORDS

***02/17/2023: It looks like they have really improved the GCP provisioning process. These instructions
may need to be rewritten (after testing the current GCP scheme).***

***When accessing your GCP account, make sure that you are authorized on the correct Google account.
Often when opening a new tab, the browser will switch back to a different account (perhaps the first one
opened?), and you can't seem to change it. I had to log out of all Google accounts in the browser,
and log in on the one that I needed.***

- This uses the Google Cloud API to drag data from a Nest thermostat and 
  send it into a [CHORDS portal](https://earthcubeprojects-chords.github.io/chords-docs/). The Nest access is managed through "Google Cloud Platform".
- Note: the Nest API was migrated from the Nest company to the Google API
  sometime in 2020, so disregard anything you see on the Internet about
  "Works With Nest".
- The Google API ecosystem is wide and deep, and it took a lot of work to figure it out.
  The biggest challenge was getting the OAuth2 authentication going. Programatically managing authorization codes and so on for OAuth2 is non-trivial.

## Developer
You will need to [register as a Google developer](https://developers.google.com/nest/device-access/registration), $5.

## Resources
I started with material from WN, but I had to do a lot to get to my final product:

His step-by-step for [creating a Google project](https://www.wouternieuwerth.nl/controlling-a-google-nest-thermostat-with-python/) with the tokens.

His [material](https://colab.research.google.com/github/WouterNieuwerth/Google-Nest-thermostat-API-example/blob/main/Google_Nest_API_thermostat_example.ipynb) on Github.

This [link](https://geoffhudik.com/tech/2023/03/04/trying-google-nest-api-with-postman-and-python/) has nice step-by-step
instructions for working with the Google `SDM` system. It looks similar to what I've documented here. It also
demonstrates using [Postman](https://www.postman.com/), which is some sort of API service. Will need
to look into Postman.

Here are Google Nest Thermostat [traits and settable modes](https://developers.google.com/nest/device-access/api/thermostat?hl=en_US).
## Workflow
This is the workflow to make this all work:

1. Create a new project on [Google Cloud Platform](https://console.cloud.google.com/device-access), 
   configuring OAuth2 credentials, and enabling the Smart Device Management (SDM) API.
1. Use the [Google Device Access Console](https:/console.nest.google.com/device-access) to
   give access to the Google API.
1. Create a URL which is used to get an authorization code for Nest. This
   is done with the `--new` option to `nest.py`.
1. Plug the authorization code into a second http request, which will
   return access and refresh tokens. This is done while `nest.py` is still running in new mode.
1. Finally, the access token may be used to get Nest data, and the refresh token
   can be used to refresh the access token.

## Setup Google API and OAuth 2.0

1. Create a new project in [Google Cloud Platform](https://console.cloud.google.com):
   - Create Resource->New Project. 
   - Once created,
   go to the dashboard for that project.
1. Go to the APIs->APIs overview.
1. Go to the OAuth Consent Screen tab. This is about the consent screen that the
   users will see in order to get a token to access the api. Make these settings
   on the configuration pages (everything else left blank):
   - External: checked
   - App name
   - Support email
   - Developer email
   - Note: don't add 'test users'; if you do the project is put into 
     test mode, and the authorization must be renewed once a week.
1. Go to the Credentials tab in the APIs & Services
   - Mash “+ Create Credentials”, and select “Create OAuth Client ID”
      - Application type: Web application
      - Name: Whatever you want
      - Authorized redirect URI `https://www.google.com` (this is where the consent screens will finally dump you; you will grab the authorization code from the URL of this page)
1. A popup will display the client ID and client secret. You can find these later on
   the same credentials tab.
1. Hit the "Publish App" button.
1. Go to the Dashboard tab.
   - Select “+ Enable APIS AND SERVICES”. 
   - Search for “Smart …”Select “Smart Device Management API”
   - Mash “Enable”

## Enable Access to Smart Data Management
1. Create a new project in the [Google Device Access Console](https:/console.nest.google.com).
   - Enter the OAuth Client ID
   - Enable the pub/sub topic.

## Getting nest.py Running
1. Edit nest.json, setting the following fields:
   - nest_console_project_id: the project id from the Device Access project.
   - client_secret: the OAuth client secret
   - client_id: the OAuth client id.

1. Intial run:
   - `python3 nest.py nest.json --new`
   - The program will pause after printing a URL. Open that URL in a browser, and
     click through everything, allowing acess, until you get to a blank google page.
     There will be many warnings about unverified application and so on. At one point
     you will need to select an 'advanced' button in order to continue.
   - Get the final URL from the browser address bar, and extract the authorization code
     from it. Enter this as the 'code' token in nest.json.
   - Hit return for nest.py. The program will now fetch access and refresh tokens, add them
     to nest.json, and then start fetching data from the thermostat.

2. Following runs:
   - `python3 nest.py nest.json`
   - The program will run using the existing access token. Every hour it will use the
     the refresh token to renew the access token, rewriting nest.json with the new one.
