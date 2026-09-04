class PlayerArea:
    # this still under development. need to find all the cases to add, remove, clear, update
    def __init__(self, json_data: dict):
        self.str_frame: str = json_data.get("strFrame", "")
        self.int_mp: int = int(json_data.get("intMP", 0))
        self.int_level: int = int(json_data.get("intLevel", 0))
        self.ent_id: int = int(json_data.get("entID", 0))
        self.str_pad: str = json_data.get("strPad", "")
        self.int_sp: int = int(json_data.get("intSP", 0))
        self.int_mp_max: int = int(json_data.get("intMPMax", 0))
        self.int_hp: int = int(json_data.get("intHP", 0))
        self.afk: bool = bool(json_data.get("afk", False))
        self.int_hp_max: int = int(json_data.get("intHPMax", 0))
        self.ty: int = int(json_data.get("ty", 0))
        self.int_sp_max: int = int(json_data.get("intSPMax", 0))
        self.tx: int = int(json_data.get("tx", 0))
        self.int_state: int = int(json_data.get("intState", 0))
        self.ent_type: str = json_data.get("entType", "")
        self.show_cloak: bool = bool(json_data.get("showCloak", True))
        self.show_helm: bool = bool(json_data.get("showHelm", True))
        self.str_username: str = json_data.get("strUsername", "")
        self.id: int = int(float(json_data.get("ID", 0)))  # scientific notation safe
        self.uo_name: str = json_data.get("uoName", "")

    def updateDataPlayer(self, json_data: dict):
        self.int_hp_max: int = int(json_data.get("intHPMax", 0))
        self.int_mp: int = int(json_data.get("intMP", 0))
        self.int_mp_max: int = int(json_data.get("intMPMax", 0))
        self.int_hp: int = int(json_data.get("intHP", 0))

    def is_hp_below(self, percent: float) -> bool:
        if self.int_hp_max <= 0:
            return False
        return (self.int_hp / self.int_hp_max) * 100 < percent