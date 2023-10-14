# VisPhoto webapp

A novel photography support system for PVI called VisPhoto.
The first key idea is to use an omnidirectional camera to take a photograph.
It allows the user not to take time to aim the camera at the target.
However, the captured image includes many objects and a large amount of background that the user does not want to include in the photograph.
Therefore, as the second key idea, in post-production,
VisPhoto generates a photograph by outputting the cropped region that the user wants to include in the photograph.
To help the user to determine which region to crop, our system applies an object detection technique to the image and provides the user with information on which objects exist in which direction.


## How to Run the application


1. Clone this repo to your local machine.
```ShellSession
% git clone git@github.com:opu-imp/VisPhoto-ASSETS-2023-tfcam.git visphoto-webapp
```

2. Launch the application.

```ShellSession
% cd visphoto-webapp
% docker compose up -d
```

3. You can access the site from http://localhost:8080