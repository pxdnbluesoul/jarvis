#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random
import sopel
import pyscp_bot.jarvis as lexicon
import re

###############################################################################


@sopel.module.commands('[^ ]+')
def autocomplete(bot, tr):
    funcs = [f for group in bot._callables.values() for f in group.values()]
    funcs = {f for l in funcs for f in l if hasattr(f, 'commands')}
    partial = tr.group(1)
    if any(partial in f.commands for f in funcs):
        return
    funcs = [
        f for f in funcs if any(c.startswith(partial) for c in f.commands)]
    if not funcs:
        return
    if len(funcs) > 1:
        names = [f.commands[0] for f in funcs]
        bot.send('Did you mean {} or {}?'.format(
            ', '.join(names[:-1]), names[-1]))
    else:
        wrapper = bot.SopelWrapper(bot, tr)
        bot.call(funcs[0], wrapper, tr)


@sopel.module.commands('choose')
def choose(bot, tr):
    """
    Randomly pick one of the options.

    The options must be comma-separated.
    """
    options = [i.strip() for i in tr.group(2).split(',')]
    bot.send(random.choice(options))


@sopel.module.rule(r'(?i)(^(?:[+-]?[0-9]*d(?:[0-9]+|f))+(?:[+-][0-9]+)?$)')
@sopel.module.commands('roll', 'dice')
def dice(bot, tr):
    groups = tr.groups()
    expr = groups[0] if len(groups) == 1 else groups[1]
    rolls = re.findall(r'([+-]?)([0-9]*)d([0-9]+|f)', expr.lower())
    total = 0
    output = []
    for sign, count, sides in rolls:
        count = 1 if not count else int(count)
        if count > 5000:
            bot.send(lexicon.die_count_too_high())
            return
        results = roll_die(sign, count, sides)
        total += sum(results)
        if sides != 'f':
            output.extend(results)
            continue
        for value in results:
            if value == 1:
                output.append('\x033+\x0F')
            elif value == -1:
                output.append('\x034-\x0F')
            else:
                output.append(0)
    bot.send('{} ({}={})'.format(total, expr, ', '.join(map(str, output))))


def roll_die(sign, count, sides):
    if sides != 'f':
        results = [random.randint(1, int(sides)) for _ in range(count)]
    else:
        results = [random.randint(-1, 1) for _ in range(count)]
    if sign == '-':
        results = [i * -1 for i in results]
    return results