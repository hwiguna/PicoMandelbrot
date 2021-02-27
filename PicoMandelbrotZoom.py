# PicoMandelbrot adapted for Pi Pico by Hari Wiguna from:
# https://www.codingame.com/playgrounds/2358/how-to-plot-the-mandelbrot-set/mandelbrot-set

def main():
    import board            # Pi Pico Board GPIO pins
    import displayio        # Python's multi layer graphics
    import adafruit_displayio_ssd1306   # OLED Driver
    import busio            # Provides I2C support
    import time
    from adafruit_display_shapes.line import Line
    #from adafruit_display_shapes.circle import Circle
    from adafruit_display_shapes.rect import Rect
    import math
    from analogio import AnalogIn
    from digitalio import DigitalInOut, Direction, Pull
    from hari.mandelbrot import mandelbrot, MAX_ITER

    WIDTH, HEIGHT = 128, 64 #32  # Change to 64 if needed
    width2 = int(WIDTH/2)
    height2 = int(HEIGHT/2)
    
    realStart, realEnd = -2-.8, 2
    imStart, imEnd = -1,1

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
        group = displayio.Group(max_size=2)

        display.show(group)

        return (display, group)

    def SetupFullScreenTileGrid():
        #-- Create a bitmap --
        bitmap = displayio.Bitmap(WIDTH, HEIGHT, 2)

        #-- Create Palette --
        palette = displayio.Palette(2)
        palette[0] = 0
        palette[1] = 0xFFFFFF

        #-- Create TileGrid --
        tileGrid = displayio.TileGrid(bitmap, pixel_shader=palette)
        return bitmap, tileGrid

    def SetupCursorTileGrid():
        #-- Create a bitmap --
        bitmap = displayio.Bitmap(WIDTH, HEIGHT, 2)

        #-- Create Palette --
        palette = displayio.Palette(2)
        palette[0] = 0
        palette[1] = 0xFFFFFF

        #-- Create TileGrid --
        tileGrid = displayio.TileGrid(bitmap, pixel_shader=palette)
        return bitmap, tileGrid

    def SetupAnalog():
        pot0 = AnalogIn(board.A0)
        pot1 = AnalogIn(board.A1)
        zoomPot = AnalogIn(board.A2)
        return (pot0, pot1, zoomPot)

    def SetupButtons():
        global buttonZoomIn, buttonZoomOut, buttonCenter
        buttonZoomIn = DigitalInOut(board.GP13)
        buttonZoomIn.direction = Direction.INPUT
        buttonZoomIn.pull = Pull.UP

        buttonZoomOut = DigitalInOut(board.GP14)
        buttonZoomOut.direction = Direction.INPUT
        buttonZoomOut.pull = Pull.UP

        buttonCenter = DigitalInOut(board.GP15)
        buttonCenter.direction = Direction.INPUT
        buttonCenter.pull = Pull.UP

    def _map(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def getCursorX(pot):
        return int(_map(pot.value, 0, 65520, 0, WIDTH))

    def getCursorY(pot):
        return int(_map(pot.value,0, 65520, 0, HEIGHT))

    def getZoomLevel(pot):
        return int(_map(pot.value, 0, 65520, 0, HEIGHT))

    def MoveCursor(display, cursor):
        if time.monotonic() >= mNextSensorRead:
            x0 = getCursorX(mPot0)
            y0 = getCursorY(mPot1)
            z = getZoomLevel(mZoomPot)
            newHeight = int(z/2)
            newWidth = int((z*WIDTH/HEIGHT)/2)
            left, right = x0-newWidth, x0+newWidth
            top, bottom = y0-newHeight, y0+newHeight
            cursor.pop()
            cursor.pop()
            cursor.pop()
            cursor.pop()
            cursor.append(Line(left,top, right,top, 0X000000)) # Top Line
            cursor.append(Line(left,top, left, bottom, 0X000000)) # Left Line
            cursor.append(Line(right,top, right, bottom, 0X000000)) # Right Line
            cursor.append(Line(left,bottom, right, bottom, 0X000000)) # Bottom Line
            display.refresh()
            mNextSensorRead = time.monotonic() + 0.1

    def ZoomIn(display, bitmap):
        if (buttonZoomIn.value == False):
            print("BEFORE:",realStart, realEnd, imStart, imEnd)
            x0 = getCursorX(mPot0)
            y0 = getCursorY(mPot1)
            z = getZoomLevel(mZoomPot)
            newHeight = int(z/2)
            newWidth = int((z*WIDTH/HEIGHT)/2)
            print(z, newWidth, newHeight)
            left, right = x0-newWidth, x0+newWidth
            top, bottom = y0-newHeight, y0+newHeight
            realRange = realEnd-realStart
            imRange = imEnd-imStart
            realStart = realStart + (realRange*left/WIDTH)
            realEnd = realStart + (right-left)*realRange/WIDTH
            imStart = imStart + (imRange*top/HEIGHT)
            imEnd = imStart + (bottom-top)*imRange/HEIGHT
            print("AFTER:",realStart, realEnd, imStart, imEnd)
            DrawMandelbrot(display, bitmap)

    def ZoomOut(display, bitmap):
        if (buttonZoomOut.value == False):
            print("BEFORE:",realStart, realEnd, imStart, imEnd)
            zoomDelta = 2
            realRange, imRange = realEnd-realStart, imEnd-imStart
            realDelta, imDelta = realRange/zoomDelta, imRange/zoomDelta
            left, right = realStart-realDelta, realEnd+realDelta
            top, bottom = imStart-imDelta, imEnd+imDelta
            realStart = left
            realEnd = right
            imStart = top
            imEnd = bottom
            print("AFTER:",realStart, realEnd, imStart, imEnd)
            DrawMandelbrot(display, bitmap)


    def Center(display, bitmap):
        if (buttonCenter.value == False):
            print("BEFORE:",realStart, realEnd, imStart, imEnd)
            realRange, imRange  = realEnd-realStart, imEnd-imStart
            width2, height2 = WIDTH/2, HEIGHT/2
            xDelta = getCursorX(mPot0) - width2
            yDelta = getCursorX(mPot1) - height2
            realDelta, imDelta = (realRange*xDelta/WIDTH), (imRange*yDelta/HEIGHT)
            realStart = realStart + realDelta
            realEnd = realEnd + realDelta
            imStart = imStart + imDelta
            imEnd = imEnd + imDelta
            print("AFTER:",realStart, realEnd, imStart, imEnd)
            DrawMandelbrot(display, bitmap)

    def DrawMandelbrot(display, bitmap):
        print("DRAWING:",realStart, realEnd, imStart, imEnd)
        RE_START = realStart
        RE_END = realEnd
        IM_START = imStart
        IM_END = imEnd

        MAX_ITER = 80
        for x in range(0, WIDTH):
            xx = RE_START + (x / WIDTH) * (RE_END - RE_START)
            for y in range(0, HEIGHT):
                yy = IM_START + (y / HEIGHT) * (IM_END - IM_START)
                c = complex(xx, yy) # Convert pixel coordinate to complex number
                m = mandelbrot(c)   # Compute the number of iterations
                color = 1 - int(m/MAX_ITER)
                bitmap[x,y] = 1 if color>0 else 0 # Plot the point
            if x % 4 == 0: display.refresh()
        display.refresh()

    #=== MAIN ===
    #global mGroup
    mPot0, mPot1, mZoomPot = SetupAnalog()
    SetupButtons()
    (mDisplay, mGroup) = SetupDisplay()
    (mBitmap, mTileGrid) = SetupFullScreenTileGrid()
    (mcBitmap, mcTileGrid) = SetupCursorTileGrid()
    mGroup.append(mTileGrid) #add the TileGrid to the group


    mCursor = displayio.Group(max_size=4)
    mCursor.append(Line(0,0, WIDTH, 0, 0X000000)) # Top Line
    mCursor.append(Line(0,0, 0, HEIGHT, 0X000000)) # Left Line
    mCursor.append(Line(WIDTH,0, WIDTH, HEIGHT, 0X000000)) # Right Line
    mCursor.append(Line(0,HEIGHT, WIDTH, HEIGHT, 0X000000)) # Bottom Line
    mGroup.append(mCursor)
    mNextSensorRead  = 0

    DrawMandelbrot(mDisplay, mBitmap)

    while True:
        MoveCursor(mDisplay,mCursor)
        ZoomIn(mDisplay, mBitmap)
        ZoomOut(mDisplay, mBitmap)
        Center(mDisplay, mBitmap)

    while True:
        pass