# VisPhoto webapp

A novel photography support system for PVI called VisPhoto.
The first key idea is to use an omnidirectional camera to take a photograph.
It allows the user not to take time to aim the camera at the target.
However, the captured image includes many objects and a large amount of background that the user does not want to include in the photograph.
Therefore, as the second key idea, in post-production,
VisPhoto generates a photograph by outputting the cropped region that the user wants to include in the photograph.
To help the user to determine which region to crop, our system applies an object detection technique to the image and provides the user with information on which objects exist in which direction.


## Source code overview

The structure of this project is shown below.
The `src` directory contains 2 apps: `sync` and `web`.

```
.
├── README.md
├── docker
├── docker-compose.yml
└── src
    ├── sync
    └── web
```

`sync`: batch application that periodically downloads omnidirectional camera images from Google Drive along with object detection and speech recognition results.

`web`: web application to crop the user's desired area from the omnidirectional camera image.


## Requirements

The applications depend on [Google Cloud API](https://cloud.google.com/apis). Thus, you should prepare your own API credentaial before starting.

In addition, `sync` app uses [Rclone](https://rclone.org/) to download files from Google Drive, so you need to set up `rclone.conf` for your Google account.


## How to run the application

1. Clone this repo to your local machine.
```ShellSession
% git clone git@github.com:opu-imp/VisPhoto-ASSETS-2023-tfcam.git visphoto-webapp
```

2. Place your Google Cloud API credentails.
```ShellSession
$ cp your-api-secret.json /src/sync/auth/VisPhoto-537053e46c2f.json
$ cp your-api-secret.json /src/web/auth/VisPhoto-537053e46c2f.json
```

3. Place your `rclone.conf`.
```ShellSession
$ mv rclone.conf src/sync/rclone
```

4. Launch the application.
```ShellSession
% cd visphoto-webapp
% docker compose up -d
```

5. You can access the site from http://localhost:8080