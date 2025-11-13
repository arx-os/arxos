/**
 * Collaboration Sidebar
 *
 * Displays collaboration rooms, active users, and provides navigation.
 */

import { useCollaborationStore } from "../state/collaborationStore";
import { MessageSquare, Users, Wifi, WifiOff, X } from "lucide-react";
import type { CollaborationRoom } from "../types";

export function CollaborationSidebar() {
  const {
    connectionState,
    rooms,
    users,
    activeRoomId,
    sidebarOpen,
    setActiveRoom,
    setSidebarOpen,
  } = useCollaborationStore();

  if (!sidebarOpen) {
    return null;
  }

  const roomList = Array.from(rooms.values());
  const userList = Array.from(users.values());
  const onlineUsers = userList.filter((u) => u.presence === "online");

  const getConnectionBadge = () => {
    switch (connectionState) {
      case "connected":
        return (
          <div className="flex items-center gap-2 text-emerald-400">
            <Wifi className="h-4 w-4" />
            <span className="text-xs">Connected</span>
          </div>
        );
      case "connecting":
      case "reconnecting":
        return (
          <div className="flex items-center gap-2 text-amber-400">
            <Wifi className="h-4 w-4 animate-pulse" />
            <span className="text-xs">Connecting...</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 text-slate-500">
            <WifiOff className="h-4 w-4" />
            <span className="text-xs">Offline</span>
          </div>
        );
    }
  };

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-slate-900 border-l border-slate-700 shadow-2xl z-40 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-slate-100">
            Collaboration
          </h2>
        </div>
        <button
          onClick={() => setSidebarOpen(false)}
          className="text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Connection Status */}
      <div className="p-4 border-b border-slate-700 bg-slate-800/50">
        {getConnectionBadge()}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Rooms Section */}
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-300">Rooms</h3>
            <span className="text-xs text-slate-500">
              {roomList.length} total
            </span>
          </div>

          {roomList.length === 0 ? (
            <div className="text-sm text-slate-500 text-center py-8">
              No rooms available
            </div>
          ) : (
            <div className="space-y-1">
              {roomList.map((room) => (
                <RoomItem
                  key={room.id}
                  room={room}
                  isActive={room.id === activeRoomId}
                  onClick={() => setActiveRoom(room.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Users Section */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-300">
              Active Users
            </h3>
            <span className="text-xs text-slate-500">
              {onlineUsers.length} online
            </span>
          </div>

          {onlineUsers.length === 0 ? (
            <div className="text-sm text-slate-500 text-center py-8">
              No users online
            </div>
          ) : (
            <div className="space-y-2">
              {onlineUsers.map((user) => (
                <div
                  key={user.did}
                  className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800/50 transition-colors"
                >
                  <div className="relative">
                    <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                      <span className="text-xs font-semibold text-blue-400">
                        {user.displayName.slice(0, 2).toUpperCase()}
                      </span>
                    </div>
                    {user.presence === "online" && (
                      <div className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-emerald-500 border-2 border-slate-900" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-200 truncate">
                      {user.displayName}
                    </div>
                    <div className="text-xs text-slate-500 truncate">
                      {user.did.slice(0, 12)}...
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface RoomItemProps {
  room: CollaborationRoom;
  isActive: boolean;
  onClick: () => void;
}

function RoomItem({ room, isActive, onClick }: RoomItemProps) {
  const hasUnread = (room.unreadCount || 0) > 0;

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors ${
        isActive
          ? "bg-blue-500/20 border border-blue-500/50"
          : "hover:bg-slate-800/50 border border-transparent"
      }`}
    >
      <div className="flex-1 min-w-0 text-left">
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-medium truncate ${
              isActive ? "text-blue-300" : "text-slate-200"
            }`}
          >
            {room.name}
          </span>
          {hasUnread && (
            <span className="flex-shrink-0 h-5 min-w-[20px] px-1.5 rounded-full bg-blue-500 text-white text-xs font-semibold flex items-center justify-center">
              {room.unreadCount}
            </span>
          )}
        </div>
        <div className="text-xs text-slate-500 truncate">
          {room.type === "direct"
            ? "Direct message"
            : room.buildingPath || room.id}
        </div>
      </div>

      <div className="flex-shrink-0 ml-2">
        <Users className="h-4 w-4 text-slate-500" />
        <span className="text-xs text-slate-500 ml-1">{room.members.length}</span>
      </div>
    </button>
  );
}
