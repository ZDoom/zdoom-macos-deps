#include <AL/alc.h>

int main()
{
    ALCdevice* device = alcOpenDevice(0);
    AEDI_EXPECT(device != nullptr);
    AEDI_EXPECT(alcGetError(device) == 0);
    AEDI_EXPECT(alcCloseDevice(device) == 1);

    return 0;
}
