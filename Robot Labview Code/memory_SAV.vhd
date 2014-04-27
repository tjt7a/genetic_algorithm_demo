-- Adafruit RGB LED Matrix Display Driver
-- Special memory for the framebuffer with separate read/write clocks
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

-- For more information on how to infer RAMs on Altera devices see this page:
-- http://quartushelp.altera.com/current/mergedProjects/hdl/vhdl/vhdl_pro_ram_inferred.htm

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;
USE ieee.std_logic_unsigned.ALL;

USE work.rgbmatrix.ALL;

ENTITY memory IS
  PORT (
    rst      : IN  STD_LOGIC;
    clk      : IN  STD_LOGIC;
    wr_start : IN  STD_LOGIC;
    wr_en    : IN  STD_LOGIC;
    wr_data  : IN  STD_LOGIC_VECTOR((DATA_WIDTH/2)-1 DOWNTO 0);
    rd_addr  : IN  STD_LOGIC_VECTOR(ADDR_WIDTH-1 DOWNTO 0);
    rd_data  : OUT STD_LOGIC_VECTOR(DATA_WIDTH-1 DOWNTO 0)
    );
END memory;

ARCHITECTURE bhv OF memory IS
  -- Internal signals
  --@@@SIGNAL waddr, next_waddr : STD_LOGIC_VECTOR(ADDR_WIDTH DOWNTO 0);  -- note: 1 more address bit
  SIGNAL waddr, waddr_ctr : STD_LOGIC_VECTOR(ADDR_WIDTH DOWNTO 0);  -- note: 1 more address bit
  --@@@CONSTANT kONE            : STD_LOGIC_VECTOR(waddr'range) := STD_LOGIC_VECTOR(to_unsigned(1, waddr'length));

  SIGNAL upper_wr_en : STD_LOGIC;
  SIGNAL lower_wr_en : STD_LOGIC;

  SIGNAL upper_rd  :  STD_LOGIC_VECTOR(wr_data'range);
  SIGNAL lower_rd  :  STD_LOGIC_VECTOR(wr_data'range);
  
  -- Inferred RAM storage signal
  TYPE half_ram IS ARRAY(0 TO 2**ADDR_WIDTH-1) OF STD_LOGIC_VECTOR(wr_data'range);
  SIGNAL upper_ram : half_ram;
  SIGNAL lower_ram : half_ram;
  
BEGIN

  -- Create an adder to calculate the next write address
  --@@@next_waddr <= STD_LOGIC_VECTOR(UNSIGNED(waddr) + 1);

  -- Update waddr_ctr
  PROCESS(rst, clk)
  BEGIN
    IF(rst = '1') THEN
      waddr_ctr <= (OTHERS => '0');         -- reset the write address to the beginning
    ELSIF(rising_edge(clk)) THEN
      IF (wr_en = '1') THEN
        waddr_ctr <= STD_LOGIC_VECTOR(UNSIGNED(waddr) + 1); -- allow the write address to increment            
      ELSE
        -- if wr_start = '1', then waddr becomes reset to '0', else it just stays the same.
        waddr_ctr <= waddr;
      END IF;
    END IF;
  END PROCESS;

  -- Handle wr_start simultaneous with wr_en (or not)
  waddr <= (OTHERS => '0') WHEN (wr_start = '1') ELSE
           waddr_ctr;

  ----------------------------------------------------------------------------------------------------------------------
  -- The following processes are specifically written in maximize the chance that they get inferred into
  -- dual-port Block Rams so as to best use the available resources.
  ----------------------------------------------------------------------------------------------------------------------
  upper_wr_en <= wr_en when (waddr(waddr'high) = '0') ELSE
                 '0';
  
  -- Write process for the upper memory
  PROCESS(clk)
  BEGIN
    IF(rising_edge(clk)) THEN
      IF (upper_wr_en = '1') THEN
        -- store input in upper pixel ram at the current write address
        upper_ram(conv_integer(waddr(waddr'high-1 DOWNTO 0))) <= wr_data;
      END IF;
    END IF;
  END PROCESS;

  
  lower_wr_en <= wr_en when (waddr(waddr'high) /= '0') ELSE
                 '0';
  
  -- Write process for the lower memory
  PROCESS(clk)
  BEGIN
    IF(rising_edge(clk)) THEN
      IF (lower_wr_en = '1') THEN
        -- store input in lower pixel ram at the current write address
        lower_ram(conv_integer(waddr(waddr'high-1 DOWNTO 0))) <= wr_data;
      END IF;
    END IF;
  END PROCESS;

  
  -- Read process for the upper memory
  PROCESS(clk)
  BEGIN
    IF(rising_edge(clk)) THEN
      upper_rd <= upper_ram(conv_integer(rd_addr));  -- retrieve contents at the given read address
    END IF;
  END PROCESS;

  -- Read process for the lower memory
  PROCESS(clk)
  BEGIN
    IF(rising_edge(clk)) THEN
      lower_rd <= lower_ram(conv_integer(rd_addr));  -- retrieve contents at the given read address
    END IF;
  END PROCESS;

  rd_data <= upper_rd & lower_rd;
  
  -- System runs at 40 MHz but is running out of resources, so save some f/f's by making rd_data combinatorial
  --@@@ output f/fs are built into block rams
  --@@@rd_data <= upper_ram(conv_integer(rd_addr)) & lower_ram(conv_integer(rd_addr));  -- retrieve contents at the given read address
  
END bhv;
