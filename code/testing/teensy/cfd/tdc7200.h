void spitick(int pin_clk);
void bitbang_byte_in(char msg_byte, int pin_din, int pin_clk);
char bitbang_byte_out(int pin_dout, int pin_clk);
void tdc_write(char cmd, char din, int pin_spi_csb, int pin_tdc_en, int pin_spi_din, int pin_spi_clk);
void tdc_read(char cmd, int pin_spi_csb, int pin_tdc_en, int pin_spi_din, 
              int pin_spi_dout, int pin_spi_clk, char* dout, int num_bytes);
void tdc_reset(int pin_tdc_en);
void tdc_start(int pin_start, int pin_latch_rstb);
void tdc_config(int pin_spi_csb, int pin_tdc_en, int pin_spi_din, int pin_spi_clk, int pin_tdc_trig);
void tdc_read_print(int pin_spi_csb, int pin_tdc_en, 
                    int pin_spi_din, int pin_spi_dout,
                    int pin_spi_clk);
bool trigg_fall(char config1);
bool stop_fall(char config1);
bool start_fall(char config1);
bool is_done(char int_status);
bool is_overflow_clk(char int_status);
bool is_overflow_coarse(char int_status);
char get_addr(char cmd);
