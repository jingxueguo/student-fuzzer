def get_initial_corpus():
    return ["fuzz"]

i = 0

def entrypoint(s):
    global i
    i += 1
    print(f'trial {i}')

    j = 0

    k = 1

    while j < 5:
        a = 0
        if len(s) > j * 5 + 2:
            while k < 10:
                if (k > 5):
                    if len(s) > k * 2:
                        if s[k+1] == 'f':
                            if s[k*2 - 1] == 's':
                                print(f'bug found after {i} trials')
                                exit(219)
                k += 1

        j += 1
    # else:
    #     if s[0] == 'a':
    #         print(f'bug found {s}')
    #         print(i)
    #         exit(219)

if __name__ == "__main__":
  for p in range(0, 110):
      entrypoint(get_initial_corpus()[0])
