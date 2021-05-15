#include <SDL.h>

int main()
{
    if (SDL_Init(SDL_INIT_EVERYTHING) != 0)
    {
        return 1;
    }

    SDL_Event dummy;

    while (SDL_PollEvent(&dummy))
    {
    }

    SDL_Quit();

    return 0;
}
