#include <SDL_mixer.h>

int main()
{
    AEDI_EXPECT(Mix_Init(0) == 0);
    AEDI_EXPECT(Mix_OpenAudio(48000, AUDIO_S16SYS, 2, 2048) == 0);
    Mix_CloseAudio();
    Mix_Quit();

    return 0;
}
