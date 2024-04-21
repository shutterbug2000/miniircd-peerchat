from .encoding import dwc_decode


class UTMMessage:
    def __init__(self, to_parse: str):
        split = to_parse.split(" ")
        if len(split) != 8:
            raise Exception(f"Unknown UTM data is longer than 8 arguments: {split}")
        # Seemingly always constant, probably some versions/size or something.
        if split[0] != "0" or split[1] != "6":
            raise Exception(
                f"Values we thought were constant were not: [{split[0]}]/[{split[1]}]"
            )
        # These seem to be overlapping message types, probably some sort of 'target'
        #
        # I've just been calling them the "System target", and "App target"
        if split[3] != "S" and split[3] != "A":
            raise Exception(f"Unknown Target: [{split[3]}]")
        type = int(split[4])
        if split[5] != "_" or not len(split[6]) == 0:
            raise Exception(
                f"2nd Unknown constants were not correct: [{split[5]}]/[{split[6]}]"
            )
        if split[2] == "B":
            value = dwc_decode(split[7])
        elif split[2] == "S":
            value = split[7]
        else:
            raise Exception(f"Unknown message encoding: {split[2]}")
        # I've got some of these parsing out but without a large user base i'm
        # not sure for real.
        self.type = type
        self.data = value
