import json
import common
from pathlib import Path

def is_monologue(name):
    return name == '' or name == 'モノローグ'

def parseArgs():
    global args
    ap = common.Args('Convert Translation JSONs to Prose')
    ap.add_argument('-dst', default='prose', help='What folder to put the results in')
    ap.add_argument('-g', '--gender', choices=['m','f'], default='f',
        help='Which gender trainer\'s lines get chosen, if present. m for male, f for female')
    args = ap.parse_args()

def convert(file):
    with open(file, encoding='utf-8') as jsonFile:
        # cursed
        output_directory = '\\'.join(file.replace('translations', args.dst).split('\\')[0:-1])
        output_destination = file.replace('translations', args.dst).replace('json', 'txt')
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        branches = 0
        with open(output_destination, 'w', encoding='utf-8') as output:
            data = json.load(jsonFile)
            # title of this chapter
            output.write('～ %s ～\n\n' % data['title'])
            last_speaker = 'none'
            branching_choices = []
            choices_shown = 1
            skip_to = -1

            for message in data['text']:
                if message['blockIdx'] < skip_to:
                    continue

                # just output female lines
                if 'trainerGender' in message and message['trainerGender'] != args.gender:
                    continue

                current_speaker = message['jpName']
                if current_speaker != last_speaker:
                    # if someone was talking, close the quotes
                    if not is_monologue(last_speaker) and last_speaker != 'none':
                        output.write('」')
                    # if nobody is talking, just add an empty line
                    if is_monologue(current_speaker):
                        if last_speaker != 'none':
                            output.write('\n\n')
                    # if somebody is talking, add dialogue marker and start quote
                    else:
                        output.write('\n\n%s: 「' % current_speaker)
                    last_speaker = current_speaker

                # add the line
                cleaned_message = message['jpText'].replace('\r', '').replace('\n', '')
                output.write(cleaned_message)
                
                # if the trainer has something to say add them in
                if 'choices' in message:
                    choices = condenseChoices(message['choices'])
                    if not is_monologue(last_speaker):
                        output.write('」')
                    output.write('\n\n')

                    if not all(choice['nextBlock'] == choices[0]['nextBlock'] for choice in choices):
                        branching_choices = list(choices)
                        skip_to = branching_choices[0]['nextBlock']
                        branching_choices.pop(0)
                        output.write('# CHOICE 1 #\n')

                    output.write('トレーナー: 「%s' % choices[0]['jpText'])
                    last_speaker = 'トレーナー'
                
                if message['nextBlock'] == -1:
                    if not is_monologue(last_speaker):
                        output.write('」')
                    
                    if len(branching_choices) > 0:
                        choices_shown += 1
                        skip_to = branching_choices[0]['nextBlock']
                        output.write('\n\n # CHOICE %d #\nトレーナー: 「%s' % (choices_shown, branching_choices.pop(0)['jpText']))
                        last_speaker = 'トレーナー'

def condenseChoices(choices:list):
    present_numbers = set()
    for choice in choices:
        present_numbers.add(choice['nextBlock'])
    condensed_choices = []

    # If two choices go to the same place, the latter choice is for female trainers
    if args.gender == "f":
        choices.reverse()

    for number in sorted(present_numbers):
        condensed_choices.append(next(i for i in choices if i['nextBlock'] == number))

    return condensed_choices

def main():
    parseArgs()

    files = common.searchFiles(args.type, args.group, args.id, args.idx, changed = args.changed)
    if not files:
        print('No files match given criteria')
        raise SystemExit
    files.sort()

    print(f'Converting group {args.group}, id {args.id}, idx {args.idx} to prose in {args.dst}...')

    for file in files:
        # So you can see it's doing something
        print(f'Converting file {file}...', end='\r')
        convert(file)
    print()
    print("Conversion complete!")

if __name__ == '__main__':
    main()