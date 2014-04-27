-- Adafruit RGB LED Matrix Display Driver
-- Finite state machine to control the LED matrix hardware
-- 
-- Copyright (c) 2012 Brian Nezvadovitz <http://nezzen.net>
-- This software is distributed under the terms of the MIT License shown below.
-- 
-- Permission is hereby granted, free of charge, to any person obtaining a copy
-- of this software and associated documentation files (the "Software"), to
-- deal in the Software without restriction, including without limitation the
-- rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
-- sell copies of the Software, and to permit persons to whom the Software is
-- furnished to do so, subject to the following conditions:
-- 
-- The above copyright notice and this permission notice shall be included in
-- all copies or substantial portions of the Software.
-- 
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
-- FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
-- IN THE SOFTWARE.

-- For some great documentation on how the RGB LED panel works, see this page:
-- http://www.rayslogic.com/propeller/Programming/AdafruitRGB/AdafruitRGB.htm
-- or this page
-- http://www.ladyada.net/wiki/tutorials/products/rgbledmatrix/index.html#how_the_matrix_works

-- S. Goadhouse  2014/04/16
--
-- Modified to use updated clk_div which was changed to output a clock enable
-- so that all of VHDL runs on the same clock domain. Also changed RGB outputs
-- so that they transition on falling edge of clk_out. This maximizes the
-- setup and hold times. clk_out, lat and oe_n are now output directly from
-- f/fs to minimize clock to output delay. Lengthed oe_n deassert time by one
-- 10 MHz period.
-- 

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;

USE work.rgbmatrix.ALL;

ENTITY ledctrl IS
  PORT (
    rst      : IN  STD_LOGIC;
    clk_in   : IN  STD_LOGIC;
    rate     : IN  STD_LOGIC_VECTOR(1 DOWNTO 0);
    -- LED Debug IO
    frame    : OUT STD_LOGIC;           -- if '1', then at the start of a frame (ie. bpp_count = 0)
    -- LED Panel IO
    clk_out  : OUT STD_LOGIC;
    rgb1     : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
    rgb2     : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
    led_addr : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
    lat      : OUT STD_LOGIC;
    oe_n     : OUT STD_LOGIC;
    -- Memory IO
    addr     : OUT STD_LOGIC_VECTOR(ADDR_WIDTH-1 DOWNTO 0);
    data     : IN  STD_LOGIC_VECTOR(DATA_WIDTH-1 DOWNTO 0)
    );
END ledctrl;

ARCHITECTURE bhv OF ledctrl IS
  -- Internal signals
  SIGNAL clk_en, clk30_en, clk20_en, clk10_en, clk05_en : STD_LOGIC;

  -- Essential state machine signals
  TYPE STATE_TYPE IS (INIT, READ_PIXEL_DATA, INCR_RAM_ADDR, LATCH, INCR_LED_ADDR);
  SIGNAL state, next_state : STATE_TYPE;

  -- State machine signals
  SIGNAL col_count, next_col_count : UNSIGNED(IMG_WIDTH_LOG2 DOWNTO 0);
  SIGNAL bpp_count, next_bpp_count : UNSIGNED(PIXEL_DEPTH-1 DOWNTO 0);
  SIGNAL s_led_addr, next_led_addr : STD_LOGIC_VECTOR(2 DOWNTO 0);
  SIGNAL s_ram_addr, next_ram_addr : STD_LOGIC_VECTOR(ADDR_WIDTH-1 DOWNTO 0);
  SIGNAL next_rgb1, next_rgb2      : STD_LOGIC_VECTOR(2 DOWNTO 0);
  SIGNAL s_oe_n, s_lat, s_clk_out  : STD_LOGIC;

  SIGNAL update_rgb : STD_LOGIC;        -- If '1', then update the RGB outputs
  SIGNAL next_frame : STD_LOGIC;        -- If '1', then clocking in pixels at start of a frame

BEGIN

  ----------------------------------------------------------------------------------------------------------------------
  -- Allow one of 4 clock speeds.
  --
  -- For a 16 x 32 RGB matrix with 8 bit pixel depth, 5 MHz clock =~ 30 frames per second
  ----------------------------------------------------------------------------------------------------------------------

  -- A simple clock divider is used here to slow down this part of the circuit
  U_CLKDIV30 : ENTITY work.clk_div
    GENERIC MAP (
      clk_in_freq  => 40000000,         -- 40MHz input clock
      clk_out_freq => 30000000          -- 30MHz output clock
      )
    PORT MAP (
      rst    => rst,
      clk_in => clk_in,
      clk_en => clk30_en
      );

  -- A simple clock divider is used here to slow down this part of the circuit
  U_CLKDIV20 : ENTITY work.clk_div
    GENERIC MAP (
      clk_in_freq  => 40000000,         -- 40MHz input clock
      clk_out_freq => 20000000          -- 20MHz output clock
      )
    PORT MAP (
      rst    => rst,
      clk_in => clk_in,
      clk_en => clk20_en
      );

  -- A simple clock divider is used here to slow down this part of the circuit
  U_CLKDIV10 : ENTITY work.clk_div
    GENERIC MAP (
      clk_in_freq  => 40000000,         -- 40MHz input clock
      clk_out_freq => 10000000          -- 10MHz output clock
      )
    PORT MAP (
      rst    => rst,
      clk_in => clk_in,
      clk_en => clk10_en
      );

  -- A simple clock divider is used here to slow down this part of the circuit
  U_CLKDIV05 : ENTITY work.clk_div
    GENERIC MAP (
      clk_in_freq  => 40000000,         -- 40MHz input clock
      clk_out_freq => 05000000          --  5MHz output clock
      )
    PORT MAP (
      rst    => rst,
      clk_in => clk_in,
      clk_en => clk05_en
      );

  -- Select when speed to run the clock enable which ultimately
  -- effects the frame rate. Note that there are 2 states per clk_out
  -- period so a 5 MHz clk_en means that clk_out essentially runs a
  -- 5 MHz / 2 = 2.5 MHz.
  clk_en <= clk30_en WHEN rate = "11" ELSE
            clk20_en WHEN rate = "10" ELSE
            clk10_en WHEN rate = "01" ELSE
            clk05_en;

  -- Breakout internal signals to the output port
  led_addr <= s_led_addr;
  addr     <= s_ram_addr;

  -- State register
  PROCESS(rst, clk_in)
  BEGIN
    IF(rst = '1') THEN
      state      <= INIT;
      col_count  <= (OTHERS => '0');
      bpp_count  <= (OTHERS => '1');    -- first state transition incrs bpp_count so start at -1 so first bpp_count = 0
      s_led_addr <= (OTHERS => '1');  -- this inits to 111 because the led_addr is actually used *after* the incoming data is latched by the panel (not while being shifted in), so by then it has been "incremented" to 000
      s_ram_addr <= (OTHERS => '0');
      frame      <= '0';
      rgb1       <= (OTHERS => '0');
      rgb2       <= (OTHERS => '0');
      oe_n       <= '1';                -- active low, so do not enable LED Matrix output
      lat        <= '0';
      clk_out    <= '0';
    ELSIF(rising_edge(clk_in)) THEN
      IF (clk_en = '1') THEN
        -- Run all f/f clocks at the slower clk_en rate
        state      <= next_state;
        col_count  <= next_col_count;
        bpp_count  <= next_bpp_count;
        s_led_addr <= next_led_addr;
        s_ram_addr <= next_ram_addr;
        frame      <= next_frame;

        IF (update_rgb = '1') THEN
          rgb1 <= next_rgb1;
          rgb2 <= next_rgb2;
        END IF;

        -- Use f/fs to eliminate variable delays due to combinatorial logic output.
        -- Also, this allows the RGB data to transition on the falling edge of
        -- clk_out in order to maximum the setup and hold times.
        oe_n    <= s_oe_n;
        lat     <= s_lat;
        clk_out <= s_clk_out;

      END IF;
    END IF;
  END PROCESS;

  -- Next-state logic
  PROCESS(state, col_count, bpp_count, s_led_addr, s_ram_addr, data) IS
    -- Internal breakouts
    VARIABLE upper, lower              : UNSIGNED(DATA_WIDTH/2-1 DOWNTO 0);
    VARIABLE upper_r, upper_g, upper_b : UNSIGNED(PIXEL_DEPTH-1 DOWNTO 0);
    VARIABLE lower_r, lower_g, lower_b : UNSIGNED(PIXEL_DEPTH-1 DOWNTO 0);
    VARIABLE r1, g1, b1, r2, g2, b2    : STD_LOGIC;
  BEGIN

    -- Pixel data is given as 2 combined words, with the upper half containing
    -- the upper pixel and the lower half containing the lower pixel. Inside
    -- each half the pixel data is encoded in RGB order with multiple repeated
    -- bits for each subpixel depending on the chosen color depth. For example,
    -- a PIXEL_DEPTH of 3 results in a 18-bit word arranged RRRGGGBBBrrrgggbbb.
    -- The following assignments break up this encoding into the human-readable
    -- signals used above, or reconstruct it into LED data signals.
    upper   := UNSIGNED(data(DATA_WIDTH-1 DOWNTO DATA_WIDTH/2));
    lower   := UNSIGNED(data(DATA_WIDTH/2-1 DOWNTO 0));
    upper_r := upper(3*PIXEL_DEPTH-1 DOWNTO 2*PIXEL_DEPTH);
    upper_g := upper(2*PIXEL_DEPTH-1 DOWNTO PIXEL_DEPTH);
    upper_b := upper(PIXEL_DEPTH-1 DOWNTO 0);
    lower_r := lower(3*PIXEL_DEPTH-1 DOWNTO 2*PIXEL_DEPTH);
    lower_g := lower(2*PIXEL_DEPTH-1 DOWNTO PIXEL_DEPTH);
    lower_b := lower(PIXEL_DEPTH-1 DOWNTO 0);

    r1 := '0'; g1 := '0'; b1 := '0';    -- Defaults
    r2 := '0'; g2 := '0'; b2 := '0';    -- Defaults

    -- Default register next-state assignments
    next_col_count <= col_count;
    next_bpp_count <= bpp_count;
    next_led_addr  <= s_led_addr;
    next_ram_addr  <= s_ram_addr;

    -- Default signal assignments
    s_clk_out  <= '0';
    s_lat      <= '0';
    s_oe_n     <= '1';                  -- this signal is "active low"
    update_rgb <= '0';
    next_frame <= '0';

    -- States
    CASE state IS
      WHEN INIT =>
        IF(s_led_addr = "111") THEN
          -- If PIXEL_DEPTH = 8, there are 255 passes per frame refresh. So to
          -- count to 255 starting from 0, when reach 254, must roll over to 0
          -- on the next count.  The reason using 255 passes instead of 256 is
          -- because 0 = 0% duty cycle and therefore 255 = 100% duty cycle.
          -- For 255 to be 100%, then it must be 255/255 and not 255/256.
          IF(bpp_count >= UNSIGNED(to_signed(-2, PIXEL_DEPTH))) THEN
            next_bpp_count <= (OTHERS => '0');
            next_frame     <= '1';          -- indicate at start of a frame
          ELSE
            next_bpp_count <= bpp_count + 1;
          END IF;
        END IF;
        next_state <= READ_PIXEL_DATA;
      WHEN READ_PIXEL_DATA =>
        -- Do parallel comparisons against BPP counter to gain multibit color
        IF(upper_r > bpp_count) THEN
          r1 := '1';
        END IF;
        IF(upper_g > bpp_count) THEN
          g1 := '1';
        END IF;
        IF(upper_b > bpp_count) THEN
          b1 := '1';
        END IF;
        IF(lower_r > bpp_count) THEN
          r2 := '1';
        END IF;
        IF(lower_g > bpp_count) THEN
          g2 := '1';
        END IF;
        IF(lower_b > bpp_count) THEN
          b2 := '1';
        END IF;
        update_rgb     <= '1';              -- clock out these new RGB values
        next_col_count <= col_count + 1;    -- update/increment column counter
        IF(col_count < IMG_WIDTH) THEN      -- check if at the rightmost side of the image
          s_oe_n     <= '0';                -- enable display while simply updating the shift register
          next_state <= INCR_RAM_ADDR;
        ELSE
          s_oe_n     <= '1';                -- disable display before latch in new LED anodes
          next_state <= INCR_LED_ADDR;
        END IF;
      WHEN INCR_RAM_ADDR =>
        s_clk_out     <= '1';               -- pulse the output clock
        s_oe_n        <= '0';               -- enable display
        next_ram_addr <= STD_LOGIC_VECTOR(UNSIGNED(s_ram_addr) + 1);
        next_state    <= READ_PIXEL_DATA;
      WHEN INCR_LED_ADDR =>
        -- display is disabled during led_addr (select lines) update
        next_led_addr  <= STD_LOGIC_VECTOR(UNSIGNED(s_led_addr) + 1);
        next_col_count <= (OTHERS => '0');  -- reset the column counter
        next_state     <= LATCH;
      WHEN LATCH =>
        -- display is disabled during latching
        s_lat      <= '1';                  -- latch the data
        next_state <= INIT;                 -- restart state machine
      WHEN OTHERS => NULL;
    END CASE;

    next_rgb1 <= r1 & g1 & b1;
    next_rgb2 <= r2 & g2 & b2;

  END PROCESS;

END bhv;
