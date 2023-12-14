# RGB Neo Pixel Application

This application allows you to control RGB Neo Pixels using an Angular front-end and a Python Flask back-end. It's designed to work with a microcontroller or Raspberry Pi with GPIO pins connected to RGB Neo Pixels.

## Prerequisites

- Microcontroller or Raspberry Pi with GPIO pins
- Neo Pixels Lights (For this app I am using WS2811, but any neopixel lights are compatible)
- Install Python 3.x on Pi
- Install Node.js and npm on Pi

## Getting Started

To quickly set up the RGB Neo Pixel application, use the provided bash script:

```bash
./setup.sh
```

This script installs the necessary dependencies, sets up the Python Flask server, and launches the Angular application.

## Running the Application

1. Start the Python Flask server:

   ```bash
   python app.py
   ```

3. Open your web browser and navigate to `http://localhost:5000/` to access the RGB Neo Pixel control interface.

## Extending Animations

The application supports extending animations for dynamic lighting effects. To add new animations, add new Animation Classes under the `animations` directory and update the Angular front-end as needed.

## Project Structure

- **`client`**: Contains the Angular application for controlling the RGB Neo Pixels.
- **`server`**: Houses the Python Flask server that interacts with the Neo Pixels and manages animations.
- **`templates`**: Holds compiled Angular code

## Running in a separate Daemon
- Run: 
   `sudo apt install nginx`

- Run: 
   `sudo nano /etc/nginx/sites-enabled/flask_app`
  
- In the open file, add the following code:
```
server {
	listen 80;
	
	location / {
		proxy_pass http://127.0.0.1:8000;
		proxy_set_header Host $host;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwareded_for;
	}
}
```

- Overwrite nginx's default config:
   `sudo unlink /etc/nginx/sites-enabled/default`

- Ensure syntax in file is correct:
   `sudo nginx -t`

- Reload nginx:
   `sudo nginx -s reload`

- Install GUnicorn3:
   `sudo apt install gunicorn3`

- Navigate to the directory you install the code add and navigate to the server directory:
   `cd ~/rgb-show/server`

- Run the app:
   `gunicorn3 app:app --daemon`

- Navigate to your pi's IP Address in your browser. You should see the app running

- To kill the app, run:
   `sudo pkill -f gunicorn3`


## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to enhance the functionality of the RGB Neo Pixel application.

## License

This project is licensed under the [MIT License](LICENSE). Feel free to use and modify it for your needs.
