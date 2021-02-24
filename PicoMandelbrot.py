# PicoMandelbrot adapted for Pi Pico by Hari Wiguna from:
# https://www.codingame.com/playgrounds/2358/how-to-plot-the-mandelbrot-set/mandelbrot-set

def main():
    import board            # Pi Pico Board GPIO pins
    import displayio        # Python's multi layer graphics
    import adafruit_displayio_ssd1306   # OLED Driver
    import busio            # Provides I2C support
    import time
    from adafruit_display_shapes.line import Line
    import math
    from hari.mandelbrot import mandelbrot, MAX_ITER

    WIDTH, HEIGHT = 128, 64 #32  # Change to 64 if needed

    displayio.release_displays() # Just to be safe

    def SetupDisplay():
        # So we can communicate with our OLED via I2C
        i2c = busio.I2C(scl=board.GP3, sda=board.GP2)
        #while not i2c.try_lock():
        #    pass
        #print("i2c address is = ",i2c.scan())

        # How displayio talks to physical screen
        display_bus = displayio.I2CDisplay(i2c, device_address=60) # was 0x3A, reset=oled_reset)

        # display represents the physical screen
        display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT, auto_refresh=False)

        # Group is a list of TileGrids that display would render on physical screen
        group = displayio.Group(max_size=1)

        display.show(group)

        return (display, group)

    def SetupTileGrid():
        #-- Create a bitmap --
        bitmap = displayio.Bitmap(WIDTH, HEIGHT, 2)

        #-- Create Palette --
        palette = displayio.Palette(2)
        palette[0] = 0
        palette[1] = 0xFFFFFF

        #-- Create TileGrid --
        tileGrid = displayio.TileGrid(bitmap, pixel_shader=palette)
        return bitmap, tileGrid


    #=== MAIN ===
    (mDisplay, mGroup) = SetupDisplay()
    (mBitmap, mTileGrid) = SetupTileGrid()
    mGroup.append(mTileGrid) #add the TileGrid to the group

    xOffset = -0.8
    RE_START = -2 + xOffset
    RE_END = 2 + xOffset
    IM_START = -1
    IM_END = 1

    MAX_ITER = 80
    for x in range(0, WIDTH):
        xx = RE_START + (x / WIDTH) * (RE_END - RE_START)
        for y in range(0, HEIGHT):
            yy = IM_START + (y / HEIGHT) * (IM_END - IM_START)
            c = complex(xx, yy) # Convert pixel coordinate to complex number
            m = mandelbrot(c)   # Compute the number of iterations
            color = 1 - int(m/MAX_ITER)
            if color>0: mBitmap[x,y] = 1 # Plot the point
        if x % 4 == 0: mDisplay.refresh()
    
    mDisplay.refresh()

    while True:
        pass