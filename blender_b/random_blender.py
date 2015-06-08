# coding=utf-8
from base_blender import *
from blender_b.connector.connect_util import ConnectUtil
from util_b.blending_util import *
from blender_b.connector.connect_simple import *

__author__ = 'DongMin Kim'


class RandomBlender(BaseBlender):
    def __init__(self, a):
        super(self.__class__, self).__init__(a)

        if BlConfig().is_use_blend_target:
            self.a_blend_target = BlendTargetCtlForDebug().get_blend_target()

        self.config = None

        self.a_chosen_atoms_list = None
        self.a_decided_atoms = None

        # TODO: change to works in several case, like 'link blending'.
        # Currently blender always makes new atom from 2 nodes.
        # 링크 같은 개념에 대해서도 동작하게 하기. 현재는 무조건 2개 노드에서만 동작.
        self.a_atom_0 = None
        self.a_atom_1 = None

        self.a_new_blended_atom = None

    def __str__(self):
        return self.__class__.__name__

    def make_default_config(self):
        default_config = {
            'ATOMS_CHOOSER': 'ChooseInSTIRange',
            'BLENDING_DECIDER': 'DecideBestSTI',
            'LINK_CONNECTOR': 'ConnectSimple'
        }
        BlConfig().make_default_config(str(self), default_config)

    def prepare_hook(self, config):
        # BlLogger().log("Start RandomBlending")
        if config is None:
            config = BlConfig().get_section(str(self))
        self.config = config

        self.a_chosen_atoms_list = None
        self.a_decided_atoms = None
        self.a_new_blended_atom = None

    def choose_atoms(self):
        self.chooser = self.chooser_finder.get_chooser(
            self.config.get('ATOMS_CHOOSER')
        )
        self.a_chosen_atoms_list = self.chooser.atom_choose()

    def decide_to_blend(self):
        self.decider = self.decider_finder.get_decider(
            self.config.get('BLENDING_DECIDER')
        )
        self.a_decided_atoms = self.decider.blending_decide(
            self.a_chosen_atoms_list
        )

    def init_new_blend_atom(self):
        # Make the blended node.
        self.a_atom_0 = self.a_decided_atoms[0]
        self.a_atom_1 = self.a_decided_atoms[1]
        self.a_new_blended_atom = ConceptNode(
            '(' +
            str(self.a_atom_0.name) + '_' + str(self.a_atom_1.name) +
            ')',
            rand_tv()
        )

    def connect_links(self):
        self.connector = self.connector_finder.get_connector(
            self.config.get('LINK_CONNECTOR')
        )

        # Detect and improve conflict links in newly blended node.
        # - Do nothing.

        # Make the links between exist nodes and newly blended node.
        # Adjust the attribute value of new links.

        # TODO: Optimize dst_info_container update period.
        # It should be move to out of src_node_list loop.
        # 타겟 정보를 담고있는 컨테이너 업데이트 주기 최적화 하기.
        # 지금은 루프 안에 있지만, 루프 밖으로 빼내야 한다.
        for src_node in self.a_decided_atoms:
            src_info_cont = ConnectUtil().make_equal_link_containers(
                self.a, src_node
            )
            dst_info_cont = ConnectUtil().make_equal_link_containers(
                self.a, self.a_new_blended_atom
            )

            exclusive_link_set = src_info_cont.s - dst_info_cont.s
            non_exclusive_link_set = src_info_cont.s & dst_info_cont.s

            self.connector.add_new_links(
                src_info_cont, exclusive_link_set, self.a_new_blended_atom
            )
            self.connector.modify_exist_links(
                src_info_cont, dst_info_cont, non_exclusive_link_set
            )

        # Make the links between source nodes and newly blended node.
        # TODO: Give proper truth value, not random.
        # 랜덤 진릿값 말고 적당한 진릿값을 주어야 한다.
        make_link_all(
            self.a,
            types.AssociativeLink,
            self.a_decided_atoms,
            self.a_new_blended_atom
        )

    def finish_hook(self):
        # DEBUG: Link with blend target.
        if BlConfig().is_use_blend_target:
            self.a.add_link(
                types.MemberLink,
                [self.a_new_blended_atom, self.a_blend_target],
                blend_target_link_tv
            )

        # DEBUG: Link with Blended Space.
        a_blended_space = \
            self.a.get_atoms_by_name(
                types.Atom,
                "BlendedSpace"
            )[0]

        self.a.add_link(
            types.MemberLink,
            [self.a_new_blended_atom, a_blended_space],
            rand_tv()
        )

        BlLogger().log(
            str(self.a_new_blended_atom.h) +
            " " +
            str(self.a_new_blended_atom.name)
        )

        self.ret = self.a_new_blended_atom
        # BlLogger().log("Finish RandomBlending")
