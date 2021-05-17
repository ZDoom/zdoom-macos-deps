#include <SDL.h>

int main()
{
    AEDI_EXPECT(SDL_Init(SDL_INIT_EVERYTHING) == 0);

    SDL_Event dummy;

    while (SDL_PollEvent(&dummy))
    {
    }

    SDL_Quit();

    return 0;
}
