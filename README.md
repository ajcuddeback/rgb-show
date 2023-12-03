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

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to enhance the functionality of the RGB Neo Pixel application.

## License

This project is licensed under the [MIT License](LICENSE). Feel free to use and modify it for your needs.
