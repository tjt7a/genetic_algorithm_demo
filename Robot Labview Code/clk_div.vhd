-- Simple parameterized clock divider that uses a counter
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
--
--
-- S. Goadhouse  2014/04/16
--
-- Modified to output a single period pulse to be used as a clock enable. This
-- way, FPGA has a single clock domain of clk_in but the circuit can still
-- operate slower using the clock enable.
-- 

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;
USE ieee.math_real.ALL;                 -- don't use for synthesis, but OK for static numbers

ENTITY clk_div IS
  GENERIC (
    clk_in_freq  : NATURAL;
    clk_out_freq : NATURAL
    );
  PORT (
    clk_in : IN  STD_LOGIC;
    rst    : IN  STD_LOGIC;
    clk_en : OUT STD_LOGIC
    );
END clk_div;

ARCHITECTURE bhv OF clk_div IS
  CONSTANT OUT_PERIOD_COUNT : INTEGER := (clk_in_freq/clk_out_freq)-1;

  -- note: integer type defaults to 32-bits wide unless you specify the range yourself  
  SIGNAL count : INTEGER RANGE 0 TO OUT_PERIOD_COUNT;
  
BEGIN
  
  PROCESS(clk_in, rst)
  BEGIN
    IF(rst = '1') THEN
      count  <= 0;
      clk_en <= '0';
    ELSIF(rising_edge(clk_in)) THEN
      IF(count = OUT_PERIOD_COUNT) THEN
        count  <= 0;
        clk_en <= '1';
      ELSE
        count  <= count + 1;
        clk_en <= '0';
      END IF;
    END IF;
  END PROCESS;

END bhv;
