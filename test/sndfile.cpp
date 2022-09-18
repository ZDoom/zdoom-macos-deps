#include <vector>
#include <sndfile.h>

int main()
{
    constexpr int CHANNELS = 1;
    constexpr int SAMPLE_RATE = 44100;
    constexpr int SAMPLE_COUNT = SAMPLE_RATE;
    constexpr int BUFFER_SIZE = SAMPLE_RATE;

    const std::vector<int> buffer(BUFFER_SIZE, 0);
    SF_INFO info = { SAMPLE_COUNT, SAMPLE_RATE, CHANNELS, SF_FORMAT_WAV | SF_FORMAT_PCM_24, 0, 0 };
    SNDFILE* file = sf_open("test.wav", SFM_WRITE, &info);

    AEDI_EXPECT(file != nullptr);
    AEDI_EXPECT(sf_write_int(file, &buffer[0], BUFFER_SIZE) == BUFFER_SIZE);
    AEDI_EXPECT(sf_close(file) == 0);

    return 0;
}
